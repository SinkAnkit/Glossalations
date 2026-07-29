# 🗣️ Glossalations

Seamless multilingual translation with audio playback — right in your browser.

## What It Does

Glossalations lets you translate text and PDF documents into 50+ languages with instant audio output. It supports both Indian and international languages, and lets you download the translated audio as MP3.

### Features

- **Text Translation** — Type or paste text, pick a target language, get instant translation + audio
- **PDF Translation** — Upload a PDF, extract text, translate and listen
- **Audio Playback & Download** — Every translation comes with text-to-speech audio you can play or save
- **Language Detection** — Automatically identifies the source language
- **Indian & World Languages** — Toggle between regional Indian languages and global ones

## Tech Stack

| Component | Library |
|-----------|---------|
| UI | Streamlit |
| Translation | deep-translator (Google Translate) |
| Text-to-Speech | gTTS |
| Language Detection | langdetect |
| PDF Parsing | PyPDF2 |

## Getting Started

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/Glossalations.git
cd Glossalations

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

## Requirements

- Python 3.8+
- Internet connection (for Google Translate & gTTS APIs)

## License

MIT
