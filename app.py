import streamlit as st
from datetime import date
from gtts import gTTS, lang
from deep_translator import GoogleTranslator
import PyPDF2
import speech_recognition as sr
from audio_recorder_streamlit import audio_recorder
import io

# --- App Configuration ---
st.set_page_config(page_title="Glossalations", page_icon="G", layout="wide")

# --- Ledger Quiet Design System ---
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
<style>
    /* === GLOBAL RESET === */
    html, body, [class*="css"],
    .stApp, .main, .block-container,
    div, span, p, label, li, td, th, h1, h2, h3, h4, h5, h6,
    input, textarea, select, button, a {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #0e1116 !important;
    }

    .stApp {
        background: #f8f9fa !important;
    }

    /* === CUSTOM CLASSES === */
    .ledger-title {
        font-size: 2rem !important;
        font-weight: 600 !important;
        line-height: 1.18 !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0 !important;
    }
    .ledger-subtitle {
        font-size: 0.9375rem !important;
        font-weight: 400 !important;
        line-height: 1.55 !important;
        color: #5b6370 !important;
        margin-top: 4px !important;
        margin-bottom: 32px !important;
    }
    .ledger-label {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: #5b6370 !important;
    }
    .ledger-sidebar-brand {
        font-size: 1.375rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.012em !important;
    }
    .ledger-sidebar-date {
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 11px !important;
        font-weight: 500 !important;
        letter-spacing: 0.06em !important;
        text-transform: uppercase !important;
        color: #5b6370 !important;
    }

    /* === TABS === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0 !important;
        border-bottom: 1px solid rgba(14,17,22,0.08) !important;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #5b6370 !important;
        padding: 12px 20px !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    .stTabs [aria-selected="true"] {
        color: #0e1116 !important;
        border-bottom: 2px solid #1f7a4d !important;
    }

    /* === BUTTONS === */
    .stButton > button,
    .stDownloadButton > button,
    .stButton > button *,
    .stDownloadButton > button * {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        border-radius: 5px !important;
        padding: 9px 18px !important;
        border: none !important;
        background: #0e1116 !important;
        color: #f8f9fa !important;
        transition: all 180ms cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
    }
    .stButton > button p,
    .stDownloadButton > button p,
    .stButton > button span,
    .stDownloadButton > button span {
        color: #f8f9fa !important;
        padding: 0 !important;
        border-radius: 0 !important;
        background: transparent !important;
    }
    .stButton > button:hover,
    .stDownloadButton > button:hover {
        background: rgba(14,17,22,0.92) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 20px -8px rgba(14,17,22,0.3) !important;
    }

    /* === TEXT INPUTS & TEXTAREAS === */
    .stTextInput input,
    .stTextArea textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        color: #0e1116 !important;
        border: 1px solid rgba(14,17,22,0.08) !important;
        border-radius: 5px !important;
        background: #ffffff !important;
    }
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    div[data-baseweb="input"] input:focus,
    div[data-baseweb="textarea"] textarea:focus {
        border-color: #0e1116 !important;
        box-shadow: 0 1px 0 0 #0e1116 !important;
    }

    /* === SELECTBOX === */
    div[data-baseweb="select"] > div {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        border: 1px solid rgba(14,17,22,0.08) !important;
        border-radius: 5px !important;
        background: #ffffff !important;
    }
    div[data-baseweb="select"] span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #0e1116 !important;
    }

    /* === RADIO BUTTONS === */
    .stRadio > div {
        font-family: 'IBM Plex Sans', sans-serif !important;
    }
    .stRadio label span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        color: #0e1116 !important;
    }

    /* === FILE UPLOADER === */
    div[data-testid="stFileUploader"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        border: 1px dashed rgba(14,17,22,0.14) !important;
        border-radius: 7px !important;
        background: #ffffff !important;
    }
    div[data-testid="stFileUploader"] p,
    div[data-testid="stFileUploader"] span,
    div[data-testid="stFileUploader"] small {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #5b6370 !important;
    }
    div[data-testid="stFileUploader"] button {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        border: 1px solid rgba(14,17,22,0.14) !important;
        border-radius: 5px !important;
        background: #ffffff !important;
        color: #0e1116 !important;
    }
    div[data-testid="stFileUploader"] button span,
    div[data-testid="stFileUploader"] button p {
        color: #0e1116 !important;
        background: transparent !important;
    }

    /* === EXPANDERS === */
    .stExpander, div[data-testid="stExpander"] {
        background: #ffffff !important;
        border: 1px solid rgba(14,17,22,0.08) !important;
        border-radius: 7px !important;
        box-shadow: rgba(14,17,22,0.04) 0 1px 2px !important;
    }
    .stExpander summary span,
    div[data-testid="stExpander"] summary span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        color: #0e1116 !important;
    }

    /* === ALERTS (success, warning, info) === */
    div[data-testid="stAlert"] {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        border-radius: 5px !important;
    }
    div[data-testid="stAlert"] p {
        font-family: 'IBM Plex Sans', sans-serif !important;
    }
    .stSuccess, div[data-baseweb="notification"][kind="positive"] {
        background: rgba(31,122,77,0.10) !important;
        border-left: 3px solid #1f7a4d !important;
    }

    /* === SIDEBAR === */
    section[data-testid="stSidebar"] {
        background: #ffffff !important;
        border-right: 1px solid rgba(14,17,22,0.08) !important;
    }
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        font-family: 'IBM Plex Sans', sans-serif !important;
    }

    /* === CAPTIONS === */
    .stCaption, div[data-testid="stCaptionContainer"] span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.8125rem !important;
        color: #5b6370 !important;
    }

    /* === SPINNER === */
    .stSpinner > div > span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        color: #5b6370 !important;
    }

    /* === DIVIDERS === */
    hr {
        border: none !important;
        border-top: 1px solid rgba(14,17,22,0.08) !important;
    }

    /* === AUDIO PLAYER === */
    .stAudio {
        border-radius: 5px !important;
    }

    /* === MARKDOWN CONTENT === */
    .stMarkdown p, .stMarkdown li, .stMarkdown span {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        line-height: 1.55 !important;
        color: #0e1116 !important;
    }
    .stMarkdown strong {
        font-weight: 600 !important;
    }

    /* === WIDGET LABELS === */
    .stWidgetLabel, div[data-testid="stWidgetLabel"] p {
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        color: #0e1116 !important;
    }

    /* === LINK BUTTONS === */
    .stLinkButton a,
    .stLinkButton a span,
    .stLinkButton a p {
        color: #f8f9fa !important;
        background: #0e1116 !important;
        font-family: 'IBM Plex Sans', sans-serif !important;
        font-size: 0.8125rem !important;
        font-weight: 500 !important;
        border-radius: 5px !important;
        text-decoration: none !important;
    }

    /* === HIDE STREAMLIT CHROME === */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}
    header[data-testid="stHeader"] {background: #f8f9fa !important;}
</style>
""", unsafe_allow_html=True)


# --- Utility Functions ---

def get_key(val):
    """Find the language code key for a given language name."""
    for key, value in lang.tts_langs().items():
        if val == value:
            return key


def categorize_languages():
    """Separate languages into Indian and World categories."""
    indian_languages = [
        'Hindi', 'Bengali', 'Telugu', 'Marathi', 'Tamil',
        'Urdu', 'Gujarati', 'Malayalam', 'Kannada', 'Odia', 'Punjabi'
    ]
    langs = lang.tts_langs()
    indian_langs = {k: v for k, v in langs.items() if v in indian_languages}
    world_langs = {k: v for k, v in langs.items() if v not in indian_languages}
    return indian_langs, world_langs


def read_pdf(file):
    """Extract text content from an uploaded PDF file."""
    pdf_reader = PyPDF2.PdfReader(file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def translate_pdf_text(pdf_text, dest_lang):
    """Translate extracted PDF text to the target language."""
    return GoogleTranslator(source='auto', target=dest_lang).translate(pdf_text)


# --- Sidebar ---

def render_sidebar():
    with st.sidebar:
        st.markdown('<p class="ledger-sidebar-brand">Glossalations</p>', unsafe_allow_html=True)
        st.caption("Breaking language barriers, one phrase at a time.")
        st.divider()
        st.markdown('<p class="ledger-label">Feedback</p>', unsafe_allow_html=True)
        feedback = st.text_area("How can we improve?", max_chars=500, label_visibility="collapsed")
        if st.button("Send", use_container_width=True) and feedback:
            st.success("Thanks for your input.")
        st.divider()
        st.markdown(
            '<p class="ledger-label">Powered by Google Translate</p>',
            unsafe_allow_html=True
        )


# --- Text Translation ---

def render_text_translation(indian_languages, world_languages):
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown('<p class="ledger-label">Source text</p>', unsafe_allow_html=True)
        input_text = st.text_area(
            "Enter text to translate", height=150, key="input_text",
            label_visibility="collapsed", placeholder="Type or paste text here..."
        )
        category = st.selectbox(
            "Category", ["Indian", "World"],
            key="text_cat", label_visibility="collapsed"
        )

    with col_output:
        st.markdown('<p class="ledger-label">Target language</p>', unsafe_allow_html=True)
        if category == "Indian":
            lang_choices = list(indian_languages.values())
        else:
            lang_choices = list(world_languages.values())
        lang_choice = st.selectbox("Pick a language", lang_choices, label_visibility="collapsed")

    if st.button("Translate", use_container_width=True, type="primary"):
        if not input_text:
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Translating..."):
                from langdetect import detect
                detected_lang = detect(input_text)

                col_det, col_trans = st.columns(2)

                with col_det:
                    st.markdown('<p class="ledger-label">Detected</p>', unsafe_allow_html=True)
                    st.info(f"{indian_languages.get(detected_lang, detected_lang)}")
                    detect_audio = gTTS(text=input_text, lang=detected_lang, slow=False)
                    detect_audio.save("user_detect.mp3")
                    with open("user_detect.mp3", "rb") as f:
                        st.audio(f.read(), format="audio/mp3")

                with col_trans:
                    st.markdown('<p class="ledger-label">Translation</p>', unsafe_allow_html=True)
                    translation = GoogleTranslator(
                        source='auto', target=get_key(lang_choice)
                    ).translate(input_text)
                    st.success(translation)
                    translated_audio = gTTS(text=translation, lang=get_key(lang_choice), slow=False)
                    translated_audio.save("user_trans.mp3")
                    with open("user_trans.mp3", "rb") as f:
                        audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    with open("user_trans.mp3", "rb") as f:
                        st.download_button(
                            "Download Audio", data=f,
                            file_name="glossalations_output.mp3",
                            mime="audio/mp3", use_container_width=True
                        )


# --- PDF Translation ---

def render_pdf_translation(indian_languages, world_languages):
    st.markdown('<p class="ledger-label">Upload document</p>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Drop a PDF here", type=["pdf"], label_visibility="collapsed")

    if uploaded_file is not None:
        pdf_text = read_pdf(uploaded_file)

        with st.expander("Extracted Text", expanded=True):
            st.text_area("PDF Content", pdf_text, height=200, disabled=True, label_visibility="collapsed")

        st.markdown('<p class="ledger-label">Target language</p>', unsafe_allow_html=True)
        category = st.selectbox(
            "Language category", ["Indian", "World"],
            key="pdf_cat", label_visibility="collapsed"
        )
        if category == "Indian":
            lang_choices = list(indian_languages.values())
        else:
            lang_choices = list(world_languages.values())

        lang_choice_pdf = st.selectbox("Translate to", lang_choices, key="lang_pdf", label_visibility="collapsed")

        if st.button("Translate Document", use_container_width=True, type="primary"):
            if not pdf_text:
                st.warning("The PDF doesn't contain extractable text.")
            else:
                with st.spinner("Translating document..."):
                    translated_text = translate_pdf_text(pdf_text, get_key(lang_choice_pdf))
                    st.success("Translation complete.")
                    st.text_area("Translated Output", translated_text, height=200, disabled=True)

                    translated_audio = gTTS(text=translated_text, lang=get_key(lang_choice_pdf), slow=False)
                    translated_audio.save("translated_pdf.mp3")
                    with open("translated_pdf.mp3", "rb") as f:
                        audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    with open("translated_pdf.mp3", "rb") as f:
                        st.download_button(
                            "Download Translated Audio", data=f,
                            file_name="glossalations_pdf.mp3",
                            mime="audio/mp3", use_container_width=True
                        )


# --- Voice Translation ---

def render_voice_translation(indian_languages, world_languages):
    st.markdown('<p class="ledger-label">Target language</p>', unsafe_allow_html=True)
    category = st.selectbox(
        "Category", ["Indian", "World"],
        key="voice_cat", label_visibility="collapsed"
    )
    if category == "Indian":
        lang_choices = list(indian_languages.values())
    else:
        lang_choices = list(world_languages.values())

    lang_choice_voice = st.selectbox(
        "Translate to", lang_choices, key="lang_voice", label_visibility="collapsed"
    )

    st.divider()
    st.markdown('<p class="ledger-label">Mode</p>', unsafe_allow_html=True)
    mode = st.selectbox("Mode", ["Record Clip", "Live"], key="voice_mode", label_visibility="collapsed")

    if mode == "Record Clip":
        render_voice_clip(lang_choice_voice)
    else:
        render_voice_live(lang_choice_voice)


def render_voice_clip(lang_choice_voice):
    """Record a clip, then transcribe and translate."""
    st.caption("Click the microphone to record. Click again to stop.")
    audio_bytes = audio_recorder(
        text="",
        recording_color="#1f7a4d",
        neutral_color="#5b6370",
        icon_size="2x",
        pause_threshold=2.5
    )

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        if st.button("Transcribe and Translate", use_container_width=True, type="primary"):
            _transcribe_and_translate(audio_bytes, lang_choice_voice)


def render_voice_live(lang_choice_voice):
    """Live transcription via WebSocket server + browser MediaRecorder."""
    st.caption("Live mode uses a local transcription server. Make sure it is running.")
    st.code("python ws_server.py", language="bash")
    st.caption("Then open the live page:")
    st.link_button("Open Live Translation", "/app/static/live.html")

def _transcribe_and_translate(audio_bytes, lang_choice_voice):
    """Shared helper: transcribe audio bytes and translate."""
    with st.spinner("Transcribing..."):
        recognizer = sr.Recognizer()
        audio_io = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_io) as source:
            audio_data = recognizer.record(source)

        try:
            transcribed_text = recognizer.recognize_google(audio_data)
        except sr.UnknownValueError:
            st.warning("Could not understand the audio. Try speaking more clearly.")
            return
        except sr.RequestError:
            st.warning("Speech recognition service is unavailable. Check your connection.")
            return

    col_src, col_out = st.columns(2)

    with col_src:
        st.markdown('<p class="ledger-label">Transcription</p>', unsafe_allow_html=True)
        st.info(transcribed_text)

    with col_out:
        with st.spinner("Translating..."):
            translation = GoogleTranslator(
                source='auto', target=get_key(lang_choice_voice)
            ).translate(transcribed_text)
            st.markdown('<p class="ledger-label">Translation</p>', unsafe_allow_html=True)
            st.success(translation)

            translated_audio = gTTS(text=translation, lang=get_key(lang_choice_voice), slow=False)
            translated_audio.save("voice_trans.mp3")
            with open("voice_trans.mp3", "rb") as f:
                st.audio(f.read(), format="audio/mp3")
            with open("voice_trans.mp3", "rb") as f:
                st.download_button(
                    "Download Audio", data=f,
                    file_name="glossalations_voice.mp3",
                    mime="audio/mp3", use_container_width=True
                )


# --- Main ---

def main():
    indian_languages, world_languages = categorize_languages()

    render_sidebar()

    st.markdown('<p class="ledger-title">Glossalations</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="ledger-subtitle">Multilingual translation with audio playback</p>',
        unsafe_allow_html=True
    )

    tab_text, tab_pdf, tab_voice = st.tabs(["Text Translation", "PDF Translation", "Voice Translation"])

    with tab_text:
        render_text_translation(indian_languages, world_languages)

    with tab_pdf:
        render_pdf_translation(indian_languages, world_languages)

    with tab_voice:
        render_voice_translation(indian_languages, world_languages)


if __name__ == "__main__":
    main()
