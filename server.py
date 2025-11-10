# server.py
import os, re, time, io, zipfile, uuid, shutil
from pathlib import Path
from typing import List, Optional, Tuple, Dict

import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pptx import Presentation
from pptx.util import Pt

# ---------- Verzeichnisse ----------
BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "static"
PUBLIC_DIR.mkdir(exist_ok=True)
BUNDLES_DIR = BASE_DIR / "bundles"
BUNDLES_DIR.mkdir(exist_ok=True)

# ---------- Provider-Konfiguration ----------
from dotenv import load_dotenv; load_dotenv()
OLLAMA_API_KEY    = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_CLOUD_BASE = os.getenv("OLLAMA_CLOUD_BASE", "https://ollama.com/v1").rstrip("/")

# ---------- Modell-Presets ----------
MODEL_PRESETS = {
    "deepseek-v3.1:671b-cloud": {"context_window": 65536,  "ideal_max": 3000, "cap": 8000, "temperature": 0.30},
    "qwen3-coder:480b-cloud":   {"context_window": 131072, "ideal_max": 1800, "cap": 8192, "temperature": 0.20},
    "glm-4.6:cloud":            {"context_window": 131072, "ideal_max": 1600, "cap": 8192, "temperature": 0.35},
    "gpt-oss:120b-cloud":       {"context_window": 65536,  "ideal_max": 1400, "cap": 8192, "temperature": 0.35},
    "qwen3-vl:235b-cloud":      {"context_window": 262144, "ideal_max": 1500, "cap": 6144, "temperature": 0.40},
    "minimax-m2:cloud":         {"context_window": 200000, "ideal_max": 1200, "cap": 8192, "temperature": 0.40},
    "gpt-oss:20b-cloud":        {"context_window": 32768,  "ideal_max": 900,  "cap": 4096, "temperature": 0.45},
}
MODEL_ALIASES = {
    "deepseek": "deepseek-v3.1:671b-cloud",
    "qwen3-coder": "qwen3-coder:480b-cloud",
    "glm-4.6": "glm-4.6:cloud",
    "gpt-oss:120b": "gpt-oss:120b-cloud",
    "qwen3-vl": "qwen3-vl:235b-cloud",
    "minimax-m2": "minimax-m2:cloud",
    "gpt-oss:20b": "gpt-oss:20b-cloud",
}

def resolve_model(name: str) -> str:
    n = (name or "").strip().lower()
    for key, canonical in MODEL_ALIASES.items():
        if key in n:
            return canonical
    return name if name in MODEL_PRESETS else "qwen3-coder:480b-cloud"

def choose_tokens_and_temp(model: str, requested_max: Optional[int], req_temp: Optional[float]):
    canon = resolve_model(model)
    preset = MODEL_PRESETS.get(canon, MODEL_PRESETS["qwen3-coder:480b-cloud"])
    cap = int(preset["cap"])
    ideal = int(preset["ideal_max"])
    chosen_max = max(300, min(int(requested_max or ideal), cap))
    temperature = float(req_temp if req_temp is not None else preset["temperature"])
    meta = {
        "model_canonical": canon,
        "context_window": preset["context_window"],
        "ideal_max": ideal,
        "cap": cap,
        "chosen_max": chosen_max,
        "temperature": temperature,
    }
    return chosen_max, temperature, meta

# ---------- App ----------
app = FastAPI(title="Website-Generator KI")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET","POST","OPTIONS"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

INDEX_FILE = BASE_DIR / "html/index.html"
WEBSITE_FILE = BASE_DIR / "html/website.html"
PPT_FILE = BASE_DIR / "html/ppt.html"

@app.get("/", response_class=HTMLResponse)
def root():
    if INDEX_FILE.exists():
        return INDEX_FILE.read_text(encoding="utf-8")
    return HTMLResponse("<h1>index.html fehlt</h1>", status_code=404)

@app.get("/website", response_class=HTMLResponse)
def website_page():
    if WEBSITE_FILE.exists():
        return WEBSITE_FILE.read_text(encoding="utf-8")
    return HTMLResponse("<h1>website.html fehlt</h1>", status_code=404)

@app.get("/ppt", response_class=HTMLResponse)
def ppt_page():
    if PPT_FILE.exists():
        return PPT_FILE.read_text(encoding="utf-8")
    return HTMLResponse("<h1>ppt.html fehlt</h1>", status_code=404)

@app.get("/health")
def health():
    return {"ok": True, "api_key_set": bool(OLLAMA_API_KEY), "base": OLLAMA_CLOUD_BASE}

# ---------- Schemas ----------
class GenReq(BaseModel):
    prompt: str
    model: Optional[str] = "qwen3-coder:480b-cloud"
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    bundle_id: Optional[str] = None
    image_names: Optional[List[str]] = None

class PptReq(BaseModel):
    topic: str
    target: Optional[str] = "Allgemeines Publikum"
    slides: Optional[int] = 10
    model: Optional[str] = "qwen3-coder:480b-cloud"
    temperature: Optional[float] = 0.25

# ---------- Helpers ----------
SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
def safe_name(name: str) -> str:
    name = SAFE_NAME_RE.sub("", name.strip().replace(" ", "_"))
    return name.lstrip(".").replace("/", "").replace("\\", "") or f"file_{uuid.uuid4().hex[:8]}"

def strip_fences(txt: str) -> str:
    if not txt: return txt
    txt = re.sub(r"^\s*```[a-zA-Z0-9]*\s*", "", txt.strip())
    txt = re.sub(r"\s*```\s*$", "", txt)
    return txt.strip()

async def call_provider(payload: dict) -> dict:
    if not OLLAMA_API_KEY:
        raise HTTPException(status_code=500, detail="OLLAMA_API_KEY fehlt")
    url = f"{OLLAMA_CLOUD_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {OLLAMA_API_KEY}", "Content-Type": "application/json"}
    limits  = httpx.Limits(max_keepalive_connections=2, max_connections=4)
    timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=20.0)
    retriable = {408, 502, 503, 504}
    async with httpx.AsyncClient(http2=False, limits=limits, timeout=timeout) as client:
        backoff = 1.0
        for attempt in range(2):
            try:
                r = await client.post(url, headers=headers, json=payload)
                if r.status_code in retriable and attempt == 0:
                    time.sleep(backoff); backoff *= 2; continue
                if r.status_code >= 400:
                    raise HTTPException(status_code=502, detail=f"Provider {r.status_code}: {r.text[:400]}")
                return r.json()
            except httpx.RequestError as e:
                if attempt == 0:
                    time.sleep(1.5); continue
                raise HTTPException(status_code=502, detail=f"Netzwerkfehler: {e}")

def ensure_bundle(bundle_id: Optional[str]) -> str:
    bid = bundle_id or uuid.uuid4().hex[:12]
    (BUNDLES_DIR / bid / "assets").mkdir(parents=True, exist_ok=True)
    return bid

def write_html(bundle_id: str, html: str) -> Path:
    out = BUNDLES_DIR / bundle_id / "index.html"
    out.write_text(html, encoding="utf-8")
    return out

def fix_img_paths_relative(html: str, image_names: List[str]) -> str:
    for name in image_names:
        base = name.split("/")[-1]
        html = re.sub(rf'(["\'(]){re.escape(base)}([)"\'])', rf'\1assets/{base}\2', html)
    return html

def absolutize_for_preview(html: str, bundle_id: str) -> str:
    return re.sub(r'(["\'(])assets/', rf'\1/bundles/{bundle_id}/assets/', html)

def ppt_outline_prompt(topic: str, target: str, slides: int) -> dict:
    system = (
        "Du bist ein Präsentations-Assistent. Antworte NUR mit JSON.\n"
        "Format:\n"
        "{\n"
        '  "title": "...",\n'
        '  "subtitle": "...",\n'
        '  "slides": [ {"title":"...","bullets":["...","..."]} ],\n'
        '  "closing": {"title":"...","bullets":["..."]}\n'
        "}\n"
    )
    user = f'Thema: "{topic}"\nZielgruppe: "{target}"\nAnzahl Inhaltsfolien: {slides} bis {slides+2}\nNur JSON, keine Erklärungen.'
    return {
        "messages": [
            {"role":"system","content":system},
            {"role":"user","content":user}
        ]
    }

def ppt_build(outline: dict) -> io.BytesIO:
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = outline.get("title","Präsentation")
    if len(s.placeholders) > 1:
        s.placeholders[1].text = outline.get("subtitle","")
    for it in outline.get("slides", []):
        sl = prs.slides.add_slide(prs.slide_layouts[1])
        sl.shapes.title.text = it.get("title","")
        body = sl.shapes.placeholders[1].text_frame
        body.clear()
        first = True
        for b in it.get("bullets", []):
            if first:
                body.text = str(b); first = False
            else:
                p = body.add_paragraph(); p.text = str(b); p.level = 0
    cl = outline.get("closing")
    if cl:
        sl = prs.slides.add_slide(prs.slide_layouts[1])
        sl.shapes.title.text = cl.get("title","Abschluss")
        body = sl.shapes.placeholders[1].text_frame
        body.clear()
        first = True
        for b in cl.get("bullets", []):
            if first: body.text = str(b); first = False
            else:     p = body.add_paragraph(); p.text = str(b); p.level = 0
    buf = io.BytesIO(); prs.save(buf); buf.seek(0); return buf

# ---------- Upload ----------
@app.post("/upload")
async def upload(files: List[UploadFile] = File(...), bundle_id: Optional[str] = Form(None)):
    bid = ensure_bundle(bundle_id)
    assets_dir = BUNDLES_DIR / bid / "assets"
    saved = []
    for uf in files:
        name = safe_name(uf.filename or "upload")
        (assets_dir / name).write_bytes(await uf.read())
        saved.append(name)
    return {"bundle_id": bid, "assets": saved}

@app.get("/bundles/{bundle_id}/assets/{filename:path}")
def serve_bundle_asset(bundle_id: str, filename: str):
    safe = safe_name(Path(filename).name)
    file_path = BUNDLES_DIR / bundle_id / "assets" / safe
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="asset not found")
    return FileResponse(str(file_path))

# ---------- Website Generate ----------
@app.post("/generate")
async def generate(req: GenReq):
    if not req.prompt:
        raise HTTPException(status_code=400, detail="prompt fehlt")

    max_tokens, temperature, picked = choose_tokens_and_temp(req.model, req.max_tokens, req.temperature)
    model = picked["model_canonical"]

    bid = ensure_bundle(req.bundle_id)
    assets_dir = BUNDLES_DIR / bid / "assets"
    images_on_disk = sorted([p.name for p in assets_dir.glob("*") if p.is_file()])
    names = [n for n in (req.image_names or images_on_disk) if (assets_dir / n).exists()]

    system = (
        "Du bist ein KI-Webdesigner. Antworte NUR mit einem vollständigen, lauffähigen "
        "HTML-Dokument inkl. eingebettetem CSS. Keine externen Skripte/Fonts.\n"
        "Wenn Bilder vorhanden sind, MUSST du sie sichtbar einbauen. "
        "Nutze dafür <img src=\"assets/NAME\" alt=\"…\"> und verwende mehrere Bereiche: "
        "Hero mit großem Bild, Galerie/Portfolio-Grid, und ggf. Feature-Sektion mit kleineren Thumbnails."
    )

    images_block = ""
    if names:
        images_block = "Verfügbare Bilder:\n" + "\n".join([f"- assets/{n}" for n in names]) + "\n"

    user = (
        f"Erstelle eine moderne One-Page basierend auf:\n\n{req.prompt}\n\n"
        f"{images_block}"
        "- Semantisches HTML, responsives CSS, dunkles Theme erlaubt.\n"
        "- Gib ausschließlich das vollständige HTML-Dokument zurück."
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    data = await call_provider(payload)
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    html = strip_fences(content)

    if "<html" not in html.lower():
        html = (
            "<!DOCTYPE html><html lang='de'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            "<title>Entwurf</title><style>body{font-family:Arial;padding:24px;max-width:900px;margin:0 auto}</style>"
            f"</head><body><h1>Entwurf</h1><pre>{content}</pre></body></html>"
        )

    html_saved = fix_img_paths_relative(html, names) if names else html
    html_preview = absolutize_for_preview(html_saved, bid)

    write_html(bid, html_saved)
    usage = data.get("usage", {}) if isinstance(data.get("usage", {}), dict) else {}
    return {
        "bundle_id": bid,
        "html": html_saved,
        "html_preview": html_preview,
        "meta": usage,
        "assets": names,
        "applied": picked
    }

# ---------- PPT Generate ----------
@app.post("/ppt_generate")
async def ppt_generate(req: PptReq):
    if not req.topic:
        raise HTTPException(status_code=400, detail="topic fehlt")

    max_tokens, temperature, picked = choose_tokens_and_temp(req.model, 1500, req.temperature)
    model = picked["model_canonical"]
    payload = {
        "model": model,
        **ppt_outline_prompt(req.topic, req.target or "Allgemeines Publikum", int(req.slides or 10)),
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    data = await call_provider(payload)
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "{}")

    m = re.search(r"\{.*\}\s*$", content, re.S)
    raw_json = m.group(0) if m else content
    try:
        outline = json.loads(raw_json)
    except Exception:
        outline = {"title": req.topic,
                   "slides":[{"title": req.topic, "bullets":["Einführung","Ziele","Überblick"]}],
                   "closing":{"title":"Abschluss","bullets":["Kernaussage","Call-to-Action"]}}
    buf = ppt_build(outline)
    headers = {"Content-Disposition": f'attachment; filename="Slides_{safe_name(req.topic)}.pptx"'}
    return StreamingResponse(buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers)

# ---------- ZIP ----------
@app.get("/bundle/{bundle_id}.zip")
def download_bundle(bundle_id: str):
    bundle_dir = BUNDLES_DIR / bundle_id
    if not bundle_dir.exists():
        raise HTTPException(status_code=404, detail="Bundle nicht gefunden")
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for path in bundle_dir.rglob("*"):
            if path.is_file():
                z.write(path, arcname=str(path.relative_to(bundle_dir)))
    mem.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="{bundle_id}.zip"'}
    return StreamingResponse(mem, media_type="application/zip", headers=headers)

# ---------- Start ----------
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("server:app", host="127.0.0.1", port=port)
