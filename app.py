import streamlit as st
from datetime import date
from gtts import gTTS, lang
from deep_translator import GoogleTranslator
import PyPDF2

# App configuration
st.set_page_config(page_title="Glossalations", page_icon="🗣️", layout="wide")

# Custom CSS for visual differentiation
st.markdown("""
<style>
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .subtitle {
        color: #888;
        font-size: 1.1rem;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 24px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)


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
    translation = GoogleTranslator(source='auto', target=dest_lang).translate(pdf_text)
    return translation


def render_sidebar():
    """Render the sidebar with branding and feedback."""
    with st.sidebar:
        st.markdown("## 🗣️ Glossalations")
        st.caption("Breaking language barriers, one phrase at a time.")
        st.divider()
        st.markdown(f"📅 **{date.today().strftime('%B %d, %Y')}**")
        st.divider()
        st.markdown("### 💬 Share Feedback")
        feedback = st.text_area("How can we improve?", max_chars=500, label_visibility="collapsed")
        if st.button("Send", use_container_width=True) and feedback:
            st.success("Thanks! We appreciate your input. 🙌")
        st.divider()
        st.caption("Powered by Google Translate & gTTS")


def render_text_translation(indian_languages, world_languages):
    """Render the text translation interface."""
    col_input, col_output = st.columns([1, 1], gap="large")

    with col_input:
        st.markdown("#### ✍️ Source")
        input_text = st.text_area("Enter text to translate", height=150, key="input_text",
                                  label_visibility="collapsed", placeholder="Type or paste text here...")
        category = st.radio("Category", ["🇮🇳 Indian", "🌍 World"], horizontal=True, label_visibility="collapsed")

    with col_output:
        st.markdown("#### 🎯 Target Language")
        if category == "🇮🇳 Indian":
            lang_choices = list(indian_languages.values())
        else:
            lang_choices = list(world_languages.values())
        lang_choice = st.selectbox("Pick a language", lang_choices, label_visibility="collapsed")

    if st.button("🔄 Translate", use_container_width=True, type="primary"):
        if not input_text:
            st.warning("Please enter some text first.")
        else:
            with st.spinner("Translating..."):
                from langdetect import detect
                detected_lang = detect(input_text)

                col_det, col_trans = st.columns(2)

                with col_det:
                    st.info(f"**Detected:** {indian_languages.get(detected_lang, detected_lang)}")
                    detect_audio = gTTS(text=input_text, lang=detected_lang, slow=False)
                    detect_audio.save("user_detect.mp3")
                    with open("user_detect.mp3", "rb") as f:
                        st.audio(f.read(), format="audio/mp3")

                with col_trans:
                    translation = GoogleTranslator(source='auto', target=get_key(lang_choice)).translate(input_text)
                    st.success(f"**Translation:** {translation}")
                    translated_audio = gTTS(text=translation, lang=get_key(lang_choice), slow=False)
                    translated_audio.save("user_trans.mp3")
                    with open("user_trans.mp3", "rb") as f:
                        audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    with open("user_trans.mp3", "rb") as f:
                        st.download_button("⬇️ Download Audio", data=f,
                                           file_name="glossalations_output.mp3",
                                           mime="audio/mp3", use_container_width=True)


def render_pdf_translation(indian_languages, world_languages):
    """Render the PDF translation interface."""
    uploaded_file = st.file_uploader("📄 Drop a PDF here", type=["pdf"])

    if uploaded_file is not None:
        pdf_text = read_pdf(uploaded_file)

        with st.expander("📖 Extracted Text", expanded=True):
            st.text_area("PDF Content", pdf_text, height=200, disabled=True, label_visibility="collapsed")

        category = st.radio("Language category", ["🇮🇳 Indian", "🌍 World"],
                            horizontal=True, key="pdf_cat", label_visibility="collapsed")
        if category == "🇮🇳 Indian":
            lang_choices = list(indian_languages.values())
        else:
            lang_choices = list(world_languages.values())

        lang_choice_pdf = st.selectbox("Translate to", lang_choices, key="lang_pdf")

        if st.button("🔄 Translate Document", use_container_width=True, type="primary"):
            if not pdf_text:
                st.warning("The PDF doesn't contain extractable text.")
            else:
                with st.spinner("Translating document..."):
                    translated_text = translate_pdf_text(pdf_text, get_key(lang_choice_pdf))
                    st.success("Translation complete!")
                    st.text_area("Translated Output", translated_text, height=200, disabled=True)

                    translated_audio = gTTS(text=translated_text, lang=get_key(lang_choice_pdf), slow=False)
                    translated_audio.save("translated_pdf.mp3")
                    with open("translated_pdf.mp3", "rb") as f:
                        audio_bytes = f.read()
                        st.audio(audio_bytes, format="audio/mp3")
                    with open("translated_pdf.mp3", "rb") as f:
                        st.download_button("⬇️ Download Translated Audio", data=f,
                                           file_name="glossalations_pdf.mp3",
                                           mime="audio/mp3", use_container_width=True)


def main():
    indian_languages, world_languages = categorize_languages()

    render_sidebar()

    # Header
    st.markdown('<p class="main-title">Glossalations</p>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Seamless multilingual translation with audio playback</p>',
                unsafe_allow_html=True)

    # Tabs instead of radio buttons
    tab_text, tab_pdf = st.tabs(["📝 Text Translation", "📄 PDF Translation"])

    with tab_text:
        render_text_translation(indian_languages, world_languages)

    with tab_pdf:
        render_pdf_translation(indian_languages, world_languages)


if __name__ == "__main__":
    main()
