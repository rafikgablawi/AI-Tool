# 🧠 AI Hub – Website- & PowerPoint-Generator

Mit dem **AI Hub** kannst du zwei mächtige Tools zentral starten:  
🌐 **Website-Generator** und 📊 **PowerPoint-Generator** – beide gesteuert über die **Ollama Cloud API** (OpenAI-kompatibel).  
Einheitliches Design, moderne Oberfläche, volle Kontrolle über KI-Modelle & Ausgabequalität.

---

<div align="center">
  <img src="static/logo.jpg" alt="Logo" width="120" style="border-radius:12px;margin-bottom:10px">
</div>

## 🚀 Features

- **🌐 Website-Generator:**  
  Erstelle komplette HTML-Onepager mit CSS – beschreibe dein Projekt, lade Bilder hoch, erhalte sofort eine fertige Website.
- **📊 PowerPoint-Generator:**  
  Generiere PPTX-Präsentationen mit automatisch strukturierten Folien, Titeln und Stichpunkten.
- **🧩 Zentrale Modell-Auswahl:**  
  Gleiche Presets für beide Tools – DeepSeek V3.1, Qwen3-Coder, GLM-4.6 u. a.
- **☁️ Ollama Cloud Support:**  
  Vollständig kompatibel mit jedem `/v1/chat/completions`-Endpoint.
- **💾 Download & Export:**  
  Websites als ZIP, Folien als PPTX – direkt per Knopfdruck.
- **🎨 Dark UI:**  
  Responsive, übersichtlich, modern.

---

## 🧠 Schnellstart

### 1️⃣ Repository klonen
```bash
git clone https://github.com/<dein-benutzername>/ai-hub.git
cd ai-hub
```

### 2️⃣ Python-Umgebung
```bash
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3️⃣ .ENV anlegen
```env
OLLAMA_API_KEY=dein_api_key
OLLAMA_CLOUD_BASE=https://ollama.com/v1
```

### 4️⃣ Server starten
```bash
python server.py
# oder
uvicorn server:app --host 0.0.0.0 --port 8000
```

➡️ [http://localhost:8000](http://localhost:8000)

---

## 🧩 Tool-Übersicht

| Tool | Beschreibung |
|------|---------------|
| 🌐 **Website-Generator** | Erzeugt vollständige HTML-Webseiten aus Text-Prompts + Bildern |
| 📊 **PowerPoint-Generator** | Baut PPTX-Folien automatisch aus einem Thema und Zielpublikum |
| ⚙️ **Modell-Presets** | Wähle passende KI je nach Anwendungsfall – Code, Text oder Bild |
| 💾 **Export** | Lade fertige Seiten oder Präsentationen herunter |
| 🧠 **KI-Optimiert** | Token-Budget & Temperature pro Modell angepasst für max. Qualität |

---

## 🧱 Projektstruktur

```
AI-Hub/
├── html/
│   ├── index.html          # Hub-Startseite
│   ├── website.html        # Website-Generator-UI
│   └── ppt.html            # PowerPoint-Generator-UI
├── static/
│   └── logo.jpg
├── server.py               # FastAPI-Backend
├── requirements.txt
└── .env
```

---

## 🧠 Backend-Spezifikation

### Voraussetzungen
- Python 3.10+
- FastAPI · Uvicorn · HTTPX · python-pptx · dotenv · pydantic

### Start
```bash
pip install -r requirements.txt
python server.py
```

### Haupt-Endpoints

#### `POST /generate`
Erzeugt HTML-Website  
**Body-Beispiel:**
```json
{
  "prompt": "Portfolio mit Galerie und Kontakt",
  "model": "qwen3-coder:480b-cloud"
}
```

#### `POST /ppt_generate`
Erstellt PPTX-Präsentation  
**Body-Beispiel:**
```json
{
  "topic": "Klimawandel Grundlagen",
  "target": "Schüler 9. Klasse",
  "slides": 10,
  "model": "deepseek-v3.1:671b-cloud"
}
```

#### `POST /upload`
Lädt Bilder für den Website-Generator.

#### `GET /bundle/{id}.zip`
Lädt fertige Website als ZIP.

---

## ⚙️ Deployment auf Render

1. Repository pushen  
2. Render → **New Web Service**
3. **Build Command**
   ```bash
   pip install -r requirements.txt
   ```
4. **Start Command**
   ```bash
   uvicorn server:app --host 0.0.0.0 --port $PORT
   ```
5. **Environment Vars**
   ```
   OLLAMA_API_KEY=<dein Key>
   OLLAMA_CLOUD_BASE=https://ollama.com/v1
   ```

---

## 🤖 Verfügbare Modelle

| Modell | Beschreibung |
|---------|---------------|
| DeepSeek V3.1 | stärkstes Gesamtmodell für Reasoning und Coding |
| Qwen3-Coder | Beste Kombination aus Code & Text |
| GLM-4.6 | Solide Balance aus Tempo & Qualität |
| GPT-OSS 120B | Robuster Allrounder |
| Qwen3-VL | Kombiniert Text + Bild |
| MiniMax M2 | Schnell und leichtgewichtig |
| GPT-OSS 20B | Kompaktes Modell für kleine Prompts |

---

## 📸 Screenshots

<div align="center">
  <img src="static/logo.jpg" width="100" alt="AI Hub Logo" style="border-radius:8px;margin:10px">
</div>

---

## 🧡 Lizenz

MIT License  
Frei nutzbar und anpassbar.

---

**Erstellt von [rafikgablawi](https://github.com/rafikgablawi)**  
*Für sauberes Design, klare UIs und strukturierte KI-Workflows.*
