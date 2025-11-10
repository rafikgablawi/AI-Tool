# 🧠 Website-Generator KI

Mit dem **Website-Generator KI** kannst du Webseiten in Sekunden automatisch via KI generieren lassen – gib einfach eine Beschreibung ein, lade Bilder hoch und wähle dein Wunsch-KI-Modell aus. Perfekt für Portfolios, Landingpages, One-Pager und mehr.

---

<div align="center">
  <img src="static/logo.jpg" alt="Logo" width="120" style="border-radius:12px;margin-bottom:10px">
</div>

## Features

- **💡 Intelligente HTML-Generierung**:  
  Beschreibe deine Wunschwebsite (z. B. "Referenzen, Hero-Bereich, Kontakt") und erhalte voll funktionsfähige, moderne HTML-Onepager mit CSS.
- **🔮 Live-Vorschau im iFrame**:  
  Das KI-generierte Ergebnis wird direkt gerendert – ohne Nachladen.
- **🧩 Flexible Modellauswahl**:  
  Setze z. B. auf DeepSeek, Qwen3-Coder, MiniMax oder GPT-OSS (über Ollama Cloud-API) – für verschiedene Zwecke und Budget wählbar.
- **🖼 Bild-Upload-Funktion**:  
  Lade beliebig viele eigene Bilder hoch, die garantiert in das Design eingebaut werden (Galerie, Hero, Thumbnails etc.).
- **⚙️ Token- und Temperature-Presets**:  
  Passe Kreativität und Output-Größe an (modellspezifisch).
- **⬇️ Download-Funktion**:  
  Exportiere Entwürfe als HTML oder als vollständiges ZIP-Bundle inkl. aller Bilder auf Knopfdruck.
- **👩‍🎨 Saubere, moderne UI**:  
  Responsive und übersichtlich gestaltet, dark mode-freundlich.

---

## Schnellstart

1. **Backend starten:**  
    Das Backend (`server.py`) ist mit FastAPI implementiert und spricht mit Ollama Cloud.  
    (Python 3.10+, siehe Setup unten)

2. **Repository klonen:**  
   ```bash
   git clone https://github.com/rafikgablawi/Website-Generator-KI.git
   cd Website-Generator-KI
   ```

3. **Frontend öffnen:**  
   `index.html` einfach im Browser öffnen.  
   *(Vollständige Funktion, inkl. Bild-Upload nur über das Backend!)*

4. **Workflow:**  
    - Websiteidee beschreiben
    - Modell wählen, optional Bilder hochladen
    - **Website erstellen** klicken!
    - Vorschau prüfen, als HTML oder ZIP speichern

---

## Backendspezifikation & API

### Voraussetzungen

- Python 3.10+
- FastAPI, Uvicorn, HTTPX
- Umgebungsvariablen:  
  - OLLAMA_API_KEY  
  - OLLAMA_CLOUD_BASE (optional, Default: https://ollama.com/v1)
- `.env` hinterlegen oder Umgebungsvariablen setzen

### Installation & Start

```bash
pip install fastapi uvicorn httpx python-dotenv pydantic
python server.py
```

Das Backend läuft anschließend auf Port 8000 (Standard).

### Wichtige Endpunkte

#### `POST /generate`

Erstellt anhand einer Beschreibung und ggf. hochgeladener Bilder ein fertiges HTML-Dokument.

```json
{
  "prompt": "Deine Wunschbeschreibung",
  "model": "Modell-Name",
  "max_tokens": 1200,
  "bundle_id": "optional",
  "image_names": ["bild3.jpg","bild1.png"]
}
```
**Response:**
```json
{
  "bundle_id": "...",
  "html": "<html>...</html>",
  "html_preview": "<html>...</html>",
  "assets": [ ... ],
  "applied": { ... }
}
```
#### `POST /upload`

Lädt Userbilder hoch, die garantiert eingebunden werden:

- `files`: Bilder (mehrfach möglich)
- `bundle_id`: optional, z. B. zum Fortsetzen bestehender Session

#### `GET /bundle/{bundle_id}.zip`

Exportiert die fertige Website inkl. Bilder als ZIP-Archiv.

---

## Beispiel-Prompts

- „Portfolio für Fotografen: Galerie, Über mich, Kontaktformular – dunkles Theme.“
- „Landingpage für eine SaaS-App: Headline, Features, Screenshots, Pricing, Call-to-Action.“
- „Business-Seite für Steuerberater, Team-Seite, Standorte, Kontakt.“

---

## Modellauswahl & Presets

Wähle aus aktuellen KI-Modellen mit unterschiedlichen Stärken (per Klick auf Kartenelement):

| Modell                    | Kontext  | Ideal Tokens | Temp | Empfehlung                       |
|---------------------------|:--------:|:------------:|:----:|----------------------------------|
| deepseek-v3.1:671b-cloud  | 64k      | 3000         | 0.30 | Stärkstes Gesamtmodell           |
| qwen3-coder:480b-cloud    | 131k     | 1800         | 0.20 | TOP für Code/HTML, Sprachlich    |
| glm-4.6:cloud             | 128k     | 1600         | 0.35 | Guter Kompromiss                 |
| gpt-oss:120b-cloud        | 64k      | 1400         | 0.35 | Allrounder                       |
| qwen3-vl:235b-cloud       | 256k     | 1500         | 0.40 | Stark für Bild+Text              |
| minimax-m2:cloud          | 200k     | 1200         | 0.40 | Leichtgewichtig, schnell         |
| gpt-oss:20b-cloud         | 32k      | 900          | 0.45 | Kleine Aufgaben                  |

---

## Screenshots

<div align="center">
  <img src="https://github.com/rafikgablawi/Website-Generator-KI/raw/main/demo_screenshot1.png" width="700" alt="UI Screenshot" style="border-radius:8px;margin:10px">
</div>

---

## Technische Hinweise

- Alle Webseitenausgaben sind **autark** (kein externes CSS/JS), daher geeignet für direktes Deployment.
- KI generiert immer vollständiges `<html>`, `<style>`, `<body>`.
- Bilder werden pfadsicher eingebettet: Preview nutzt absolute, Download relativ-Pfade (`assets/…`).
- Alle hochgeladenen Assets werden im ZIP bereitgestellt.

---

## Lizenz

MIT

---

**Erstellt von [rafikgablawi](https://github.com/rafikgablawi)**
