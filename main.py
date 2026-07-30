"""
Glossalations - FastAPI backend
Serves the frontend and handles translation, PDF extraction, voice clip, OCR,
conversation mode, live transcription, and AI summarization.
Uses Groq Whisper API for high-quality multilingual transcription.
"""
import io
import os
import hashlib
import tempfile
import httpx
from pathlib import Path
from collections import OrderedDict

from fastapi import FastAPI, UploadFile, File, Form, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from gtts import gTTS, lang
from deep_translator import GoogleTranslator
from langdetect import detect
from pydub import AudioSegment
import speech_recognition as sr
import PyPDF2
from unidecode import unidecode

app = FastAPI(title="Glossalations")

# Static directory path
STATIC_DIR = Path(__file__).parent / "static"

# Groq API key (set as environment variable)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

recognizer = sr.Recognizer()


# --- Translation Cache (LRU, in-memory) ---
class TranslationCache:
    def __init__(self, maxsize=500):
        self._cache = OrderedDict()
        self._maxsize = maxsize

    def get(self, text, target):
        key = hashlib.md5(f"{text}:{target}".encode()).hexdigest()
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def put(self, text, target, translation, romanized=None):
        key = hashlib.md5(f"{text}:{target}".encode()).hexdigest()
        self._cache[key] = {"translation": translation, "romanized": romanized}
        self._cache.move_to_end(key)
        if len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)

cache = TranslationCache()


# --- Groq Whisper Transcription ---

def transcribe_with_groq(audio_bytes, format="wav"):
    """Transcribe audio using Groq Whisper API (whisper-large-v3-turbo)."""
    if not GROQ_API_KEY:
        return None

    suffix = f".{format}"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(audio_bytes)
    tmp.close()

    try:
        with open(tmp.name, "rb") as f:
            response = httpx.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": (f"audio{suffix}", f, f"audio/{format}")},
                data={
                    "model": "whisper-large-v3-turbo",
                    "response_format": "json"
                },
                timeout=30.0
            )

        if response.status_code == 200:
            result = response.json()
            text = result.get("text", "").strip()
            return text if text else None
        else:
            print(f"Groq Whisper error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Groq Whisper failed: {e}")
        return None
    finally:
        os.unlink(tmp.name)


# --- Groq LLM Summarization ---

def summarize_text(text, language="en"):
    """Summarize text using Groq LLM API."""
    if not GROQ_API_KEY:
        return None

    lang_instruction = ""
    if language and language != "en":
        lang_instruction = " Respond in the same language as the input text."

    try:
        response = httpx.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [
                    {
                        "role": "system",
                        "content": f"You are a concise summarizer. Provide a brief summary of the given text in 2-3 sentences. Capture the key points.{lang_instruction}"
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                "max_tokens": 300,
                "temperature": 0.3
            },
            timeout=15.0
        )

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()
        else:
            print(f"Groq LLM error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Groq summarize failed: {e}")
        return None


# --- OCR ---

def extract_text_from_image(image_bytes):
    """Extract text from image using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        if text.strip():
            return text.strip()
    except ImportError:
        pass
    except Exception:
        pass
    return None


# --- Utility ---

def get_supported_languages():
    """Return supported TTS languages."""
    return lang.tts_langs()

def translate_text_cached(text, target):
    """Translate with caching."""
    cached = cache.get(text, target)
    if cached:
        return cached["translation"], cached["romanized"]

    translation = GoogleTranslator(source="auto", target=target).translate(text)
    romanized = unidecode(translation) if target != "en" else None
    cache.put(text, target, translation, romanized)
    return translation, romanized

def transcribe_audio(audio_bytes, format="webm"):
    """Transcribe audio: Groq Whisper first, Google Speech fallback."""
    audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format=format)
    audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)
    wav_buffer = io.BytesIO()
    audio_segment.export(wav_buffer, format="wav")
    wav_buffer.seek(0)
    wav_bytes = wav_buffer.getvalue()

    # Try Groq Whisper first (better accuracy, Indic language support)
    groq_result = transcribe_with_groq(wav_bytes, format="wav")
    if groq_result:
        return groq_result

    # Fallback to Google Speech
    wav_buffer.seek(0)
    try:
        with sr.AudioFile(wav_buffer) as source:
            audio_data = recognizer.record(source)
        text = recognizer.recognize_google(audio_data)
        return text
    except sr.UnknownValueError:
        pass
    except sr.RequestError:
        pass

    return None


# --- Routes ---

@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/conversation")
async def conversation_page():
    return FileResponse(STATIC_DIR / "conversation.html")


@app.get("/api/languages")
async def languages():
    """Return available languages."""
    langs = get_supported_languages()
    return JSONResponse(content=langs)


@app.post("/api/translate-text")
async def translate_text_endpoint(text: str = Form(...), target: str = Form(...)):
    """Translate text and return translation + audio URL."""
    detected = detect(text)
    translation, romanized = translate_text_cached(text, target)

    # Generate TTS audio
    tts = gTTS(text=translation, lang=target, slow=False)
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tts.save(audio_path.name)

    response = {
        "detected_language": detected,
        "translation": translation,
        "audio_url": f"/api/audio/{os.path.basename(audio_path.name)}"
    }
    if romanized:
        response["romanized"] = romanized

    return JSONResponse(content=response)


@app.post("/api/translate-pdf")
async def translate_pdf(file: UploadFile = File(...), target: str = Form(...)):
    """Extract text from PDF, translate, return result + audio."""
    content = await file.read()
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
    text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    text = text.strip()
    if not text:
        return JSONResponse(content={"error": "No text found in PDF"}, status_code=400)

    translation, romanized = translate_text_cached(text, target)

    tts = gTTS(text=translation, lang=target, slow=False)
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tts.save(audio_path.name)

    response = {
        "original_text": text,
        "translation": translation,
        "audio_url": f"/api/audio/{os.path.basename(audio_path.name)}"
    }
    if romanized:
        response["romanized"] = romanized

    return JSONResponse(content=response)


@app.post("/api/translate-clip")
async def translate_clip(file: UploadFile = File(...), target: str = Form(...)):
    """Transcribe an audio clip, translate, return result + audio."""
    content = await file.read()

    try:
        transcript = transcribe_audio(content, format="webm")
    except Exception as e:
        return JSONResponse(content={"error": f"Audio processing failed: {str(e)}"}, status_code=400)

    if not transcript:
        return JSONResponse(content={"error": "Could not understand audio. Try speaking louder or clearer."}, status_code=400)

    detected = detect(transcript)
    translation, romanized = translate_text_cached(transcript, target)

    # TTS
    tts = gTTS(text=translation, lang=target, slow=False)
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tts.save(audio_path.name)

    response = {
        "transcript": transcript,
        "detected_language": detected,
        "translation": translation,
        "audio_url": f"/api/audio/{os.path.basename(audio_path.name)}"
    }
    if romanized:
        response["romanized"] = romanized

    return JSONResponse(content=response)


@app.post("/api/translate-ocr")
async def translate_ocr(file: UploadFile = File(...), target: str = Form(...)):
    """Extract text from image via OCR, translate."""
    content = await file.read()

    extracted = extract_text_from_image(content)
    if not extracted:
        return JSONResponse(content={"error": "No text found in image. Make sure the image contains readable text."}, status_code=400)

    detected = detect(extracted)
    translation, romanized = translate_text_cached(extracted, target)

    # TTS
    tts = gTTS(text=translation, lang=target, slow=False)
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tts.save(audio_path.name)

    response = {
        "extracted_text": extracted,
        "detected_language": detected,
        "translation": translation,
        "audio_url": f"/api/audio/{os.path.basename(audio_path.name)}"
    }
    if romanized:
        response["romanized"] = romanized

    return JSONResponse(content=response)


@app.post("/api/conversation")
async def conversation_translate(
    file: UploadFile = File(...),
    source_lang: str = Form(...),
    target_lang: str = Form(...)
):
    """Conversation mode: transcribe speech, translate to other person's language."""
    content = await file.read()

    try:
        transcript = transcribe_audio(content, format="webm")
    except Exception as e:
        return JSONResponse(content={"error": f"Audio failed: {str(e)}"}, status_code=400)

    if not transcript:
        return JSONResponse(content={"error": "Could not understand audio. Try again."}, status_code=400)

    translation, romanized = translate_text_cached(transcript, target_lang)

    # TTS in target language
    tts = gTTS(text=translation, lang=target_lang, slow=False)
    audio_path = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False, dir="/tmp")
    tts.save(audio_path.name)

    response = {
        "transcript": transcript,
        "translation": translation,
        "audio_url": f"/api/audio/{os.path.basename(audio_path.name)}"
    }
    if romanized:
        response["romanized"] = romanized

    return JSONResponse(content=response)


@app.post("/api/summarize")
async def summarize_endpoint(text: str = Form(...)):
    """Summarize text using Groq LLM."""
    if not text.strip():
        return JSONResponse(content={"error": "No text provided"}, status_code=400)

    if not GROQ_API_KEY:
        return JSONResponse(content={"error": "Summarization not available (API key not configured)"}, status_code=503)

    detected = detect(text)
    summary = summarize_text(text, language=detected)

    if not summary:
        return JSONResponse(content={"error": "Summarization failed. Try again."}, status_code=500)

    return JSONResponse(content={"summary": summary, "language": detected})


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """Serve generated audio files."""
    filename = os.path.basename(filename)
    filepath = f"/tmp/{filename}"
    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="audio/mpeg")
    return JSONResponse(content={"error": "File not found"}, status_code=404)


# --- WebSocket: Live Transcription ---

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    """Handle live audio streaming, transcription, and translation."""
    await websocket.accept()
    target_lang = "hi"
    cumulative_text = ""

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            # Text message = config
            if "text" in message:
                import json
                try:
                    data = json.loads(message["text"])
                    if "target_lang" in data:
                        target_lang = data["target_lang"]
                    if data.get("action") == "clear":
                        cumulative_text = ""
                        await websocket.send_json({
                            "transcript": "",
                            "translation": "",
                            "status": "cleared"
                        })
                except Exception:
                    pass
                continue

            # Binary message = audio chunk
            if "bytes" in message:
                audio_bytes = message["bytes"]
                if len(audio_bytes) < 500:
                    continue

                try:
                    text = transcribe_audio(audio_bytes, format="webm")
                    if text:
                        cumulative_text += " " + text
                        cumulative_text = cumulative_text.strip()

                        translation, romanized = translate_text_cached(cumulative_text, target_lang)

                        response = {
                            "transcript": cumulative_text,
                            "translation": translation,
                            "status": "ok",
                            "latest": text
                        }
                        if romanized:
                            response["romanized"] = romanized

                        await websocket.send_json(response)
                    else:
                        await websocket.send_json({
                            "transcript": cumulative_text,
                            "translation": "",
                            "status": "listening"
                        })

                except Exception as e:
                    await websocket.send_json({
                        "transcript": cumulative_text,
                        "translation": "",
                        "status": "error",
                        "message": str(e)
                    })

    except WebSocketDisconnect:
        pass
    except RuntimeError:
        pass


# Mount static files AFTER all routes so it doesn't shadow them
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
