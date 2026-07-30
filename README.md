# Glossalations

A multilingual translation web app with real-time voice transcription, OCR, conversation mode, and audio playback.

**Live Demo:** https://glossalations.onrender.com

## Features

- Text translation with auto-detected source language
- PDF document extraction and translation
- Voice clip recording, transcription, and translation
- Image/OCR - upload photos of text (signs, menus, documents) to extract and translate
- Live real-time transcription and translation via WebSocket
- Conversation mode - two-way live translation for speaking with someone in another language
- AI-powered summarization of transcriptions and text
- Whisper-large-v3-turbo transcription via Groq (high accuracy, Indic language support)
- Romanized output for non-English translations
- Translation history stored locally
- Dark/light theme
- Copy and download translations
- Audio playback of translated text (TTS)
- PWA support - installable on mobile

## Tech Stack

- Backend: Python, FastAPI, Uvicorn
- Speech Recognition: Groq Whisper API (whisper-large-v3-turbo) with Google Speech fallback
- Summarization: Groq LLM (Llama 3.1)
- Translation: Google Translate (via deep-translator)
- OCR: Tesseract
- TTS: gTTS
- Frontend: Vanilla HTML/CSS/JS
- WebSocket for live streaming

## Setup

### Prerequisites

- Python 3.10+
- Tesseract OCR (for image translation)
- Groq API key (free at https://console.groq.com)

Install Tesseract:

```bash
# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# macOS
brew install tesseract
```

### Install

```bash
git clone https://github.com/SinkAnkit/Glossalations.git
cd Glossalations
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables

```bash
export GROQ_API_KEY="your-groq-api-key-here"
```

### Run

```bash
python main.py
```

Visit http://localhost:8000

### Notes

- Use `localhost:8000` (not `0.0.0.0:8000`) so the browser allows microphone access
- If GROQ_API_KEY is not set, transcription falls back to Google Speech API (less accurate)
- For HTTPS (needed on some browsers for mic):
  ```bash
  openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
  uvicorn main:app --host 0.0.0.0 --port 8000 --ssl-keyfile key.pem --ssl-certfile cert.pem
  ```

## Project Structure

```
Glossalations/
  main.py              - FastAPI backend (all API routes + WebSocket)
  requirements.txt     - Python dependencies
  Dockerfile           - Docker config for deployment
  static/
    index.html         - Main app page
    conversation.html  - Conversation mode page
    app.js             - Frontend logic
    style.css          - Styles (light/dark theme)
    manifest.json      - PWA manifest
    service-worker.js  - PWA offline caching
```

## Deployment

Deployed on Render using Docker. The Dockerfile installs tesseract-ocr and ffmpeg as system dependencies. Set `GROQ_API_KEY` as an environment variable in Render's dashboard.

## License

MIT
