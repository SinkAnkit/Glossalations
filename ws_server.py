"""
WebSocket server for real-time audio transcription and translation.
Receives audio chunks from the browser, transcribes them, translates, and sends results back.
"""
import asyncio
import json
import io
import websockets
import speech_recognition as sr
from deep_translator import GoogleTranslator
from pydub import AudioSegment
from unidecode import unidecode

recognizer = sr.Recognizer()
recognizer.energy_threshold = 200  # Lower threshold to catch speech after pauses
recognizer.dynamic_energy_threshold = False


async def handle_client(websocket):
    """Handle a single WebSocket client connection."""
    target_lang = "hi"  # default
    cumulative_text = ""

    async for message in websocket:
        # Check if it's a config message (JSON)
        if isinstance(message, str):
            try:
                data = json.loads(message)
                if "target_lang" in data:
                    target_lang = data["target_lang"]
                if data.get("action") == "clear":
                    cumulative_text = ""
                    await websocket.send(json.dumps({
                        "transcript": "",
                        "translation": "",
                        "status": "cleared"
                    }))
                continue
            except json.JSONDecodeError:
                continue

        # It's binary audio data (WebM from browser)
        audio_bytes = message

        if len(audio_bytes) < 500:
            continue

        try:
            # Convert WebM to WAV for speech_recognition
            audio_segment = AudioSegment.from_file(io.BytesIO(audio_bytes), format="webm")
            audio_segment = audio_segment.set_channels(1).set_frame_rate(16000)

            # Strip leading/trailing silence to help recognizer catch short phrases
            from pydub.silence import detect_nonsilent
            nonsilent = detect_nonsilent(audio_segment, min_silence_len=300, silence_thresh=-40)
            if nonsilent:
                start_ms = max(0, nonsilent[0][0] - 100)
                end_ms = min(len(audio_segment), nonsilent[-1][1] + 100)
                audio_segment = audio_segment[start_ms:end_ms]
            else:
                # Entire chunk is silence, skip
                await websocket.send(json.dumps({
                    "transcript": cumulative_text,
                    "translation": "",
                    "status": "no_speech"
                }))
                continue

            wav_buffer = io.BytesIO()
            audio_segment.export(wav_buffer, format="wav")
            wav_buffer.seek(0)

            with sr.AudioFile(wav_buffer) as source:
                audio_data = recognizer.record(source)

            text = recognizer.recognize_google(audio_data)
            if text:
                cumulative_text += " " + text
                cumulative_text = cumulative_text.strip()

                # Translate
                try:
                    translation = GoogleTranslator(
                        source='auto', target=target_lang
                    ).translate(cumulative_text)
                    romanized = unidecode(translation) if target_lang != "en" else None
                except Exception:
                    translation = "(translation error)"
                    romanized = None

                response = {
                    "transcript": cumulative_text,
                    "translation": translation,
                    "status": "ok",
                    "latest": text
                }
                if romanized:
                    response["romanized"] = romanized

                await websocket.send(json.dumps(response))

        except sr.UnknownValueError:
            await websocket.send(json.dumps({
                "transcript": cumulative_text,
                "translation": "",
                "status": "no_speech"
            }))
        except sr.RequestError as e:
            await websocket.send(json.dumps({
                "transcript": cumulative_text,
                "translation": "",
                "status": "error",
                "message": f"Recognition service error: {str(e)}"
            }))
        except Exception as e:
            await websocket.send(json.dumps({
                "transcript": cumulative_text,
                "translation": "",
                "status": "error",
                "message": str(e)
            }))



async def main():
    print("Transcription WebSocket server starting on ws://localhost:8502")
    async with websockets.serve(handle_client, "localhost", 8502):
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    asyncio.run(main())
