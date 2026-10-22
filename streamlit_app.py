"""
Sign Language Assistive Suite - Bilingual Web Dashboard (Tamil & English)
Streamlit-powered interactive portal featuring both pipelines:
  1. Sign Language to Audio (Vision AI, Real-Time Translation, Tamil & English Speech)
  2. Text & Speech to Sign Language (English & Tamil Text ➔ Animated Hand Skeleton Diagrams)
  3. Interactive Bilingual Dictionary & Speech Synthesizer Studio
"""

import os
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message=r".*SymbolDatabase\.GetPrototype.*")

import streamlit as st
import numpy as np
import pandas as pd
from PIL import Image
import cv2

from src.text_to_sign import TextToSignEngine
from src.tts_engine import TTSEngine
from src.translator import BilingualTranslator

st.set_page_config(
    page_title="Bilingual Sign Language Assistive Suite",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(90deg, #00d2ff, #3a7bd5);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #8d99ae;
        font-size: 1.05rem;
        font-style: italic;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #1e222d;
        border-radius: 10px;
        padding: 15px;
        border: 1px solid #2a3040;
        text-align: center;
    }
    .tamil-tag {
        background-color: #0077b6;
        color: #ffffff;
        padding: 3px 8px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">🤟 Bi-Directional Sign Language Assistive Suite</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Sign Language ➔ Tamil & English Audio Speech  |  Text & Voice ➔ Visual Sign Gestures</p>', unsafe_allow_html=True)
st.write("---")

# Navigation Sidebar
sidebar_nav = st.sidebar.radio(
    "Navigation Menu",
    [
        "🌐 Social Impact & Overview",
        "📹 Sign Language to Audio (Tamil & English)",
        "✍️ Text & Speech to Sign Language",
        "📖 Bilingual Sign Dictionary & Flashcards",
        "🔊 Speech Synthesizer Studio"
    ]
)

@st.cache_resource
def get_engine():
    return TextToSignEngine()

@st.cache_resource
def get_tts():
    return TTSEngine(rate=160, volume=1.0, default_lang="ta")

engine = get_engine()
tts = get_tts()

# -----------------------------------------------------------------------------
# 1. Social Impact & Overview
# -----------------------------------------------------------------------------
if sidebar_nav == "🌐 Social Impact & Overview":
    st.header("🌍 The Social Problem & Bi-Directional Vision")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("""
        ### Why Bi-Directional Bilingual Communication is Essential
        Communication is inherently a two-way exchange. Over **70 million deaf individuals** worldwide use sign language as their primary tongue.

        Existing systems frequently have two critical limitations:
        1. **One-Way Only**: Only translate sign-to-text, leaving deaf individuals unable to understand hearing people's replies.
        2. **Language Barrier**: Primarily focused on English, ignoring major regional languages like **Tamil (தமிழ்)** spoken by over **80 million people**.

        ### Our Integrated Solution
        * **Deaf ➔ Hearing User**: Webcam detects 3D hand landmarks in real time, classifies signs, and speaks naturally in **Tamil (தமிழ்)** and **English**!
        * **Hearing ➔ Deaf User**: Type a sentence in English or Tamil, or speak into a microphone; the system parses the phrase and renders sequential visual hand skeleton diagrams and animations.
        """)

        st.info("💡 **Inclusive & Accessible**: Runs on standard laptops and mobile browsers. No expensive data gloves or specialized hardware needed.")

    with col2:
        st.subheader("Key Impact Metrics")
        st.metric(label="Global Deaf Population", value="70+ Million")
        st.metric(label="Tamil Speakers Worldwide", value="80+ Million")
        st.metric(label="Communication Paradigm", value="Bi-Directional (2-Way)")
        st.metric(label="Languages Supported", value="Tamil (தமிழ்) & English")
        st.metric(label="Hardware Required", value="Standard Camera & Mic")

# -----------------------------------------------------------------------------
# 2. Sign Language to Audio (Tamil & English)
# -----------------------------------------------------------------------------
elif sidebar_nav == "📹 Sign Language to Audio (Tamil & English)":
    st.header("📹 Sign Language to Audio (Tamil & English)")
    st.markdown("Test gesture recognition from live webcam input or uploaded photo, with bilingual translation and speech synthesis:")

    tab_cam, tab_sample = st.tabs(["📸 Webcam Snapshot / Test", "💡 Pre-recorded Gesture Samples"])

    with tab_cam:
        col_cam, col_res = st.columns([1, 1])

        with col_cam:
            st.subheader("Camera Input")
            img_file = st.camera_input("Capture a hand sign gesture:")

        with col_res:
            st.subheader("Detection & Translation Results")
            if img_file is not None:
                bytes_data = img_file.getvalue()
                cv_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

                from src.hand_detector import HandDetector
                from src.gesture_classifier import GestureClassifier

                detector = HandDetector(max_hands=1)
                classifier = GestureClassifier()

                processed, lm_list, bbox = detector.find_landmarks(cv_img, draw=True)

                if lm_list:
                    norm_feat = detector.get_normalized_landmarks(lm_list)
                    hand_type = detector.get_hand_type(processed)
                    label, conf, src = classifier.classify(norm_feat, lm_list, hand_type)

                    tamil_text, translit = BilingualTranslator.get_sign_tamil(label)

                    st.success(f"### Detected Sign: **{label}**")
                    st.markdown(f"#### **Tamil:** <span class='tamil-tag'>{tamil_text}</span> *({translit})*", unsafe_allow_html=True)
                    st.progress(conf)
                    st.caption(f"Confidence: {int(conf * 100)}% | Engine: {src}")

                    # Speech buttons
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        if st.button("🔊 தமிழ் குரல் (Speak Tamil)", key="btn_ta_cam"):
                            tts.speak(tamil_text, lang='ta')
                            st.toast(f"Speaking Tamil: {tamil_text}")
                    with col_b2:
                        if st.button("🔊 Speak English", key="btn_en_cam"):
                            tts.speak(label, lang='en')
                            st.toast(f"Speaking English: {label}")
                else:
                    st.warning("No hand detected. Please hold your hand clearly in front of the camera.")
            else:
                st.info("Point your webcam at your hand and take a snapshot to recognize the sign!")

    with tab_sample:
        st.subheader("Interactive Quick-Test Gestures")
        sample_signs = list(BilingualTranslator.SIGN_VOCABULARY.keys())
        selected_sign = st.selectbox("Select a sign gesture to test translation and audio:", sample_signs)

        col_img, col_info = st.columns([1, 1])
        with col_img:
            img_path = os.path.join(engine.assets_dir, f"{selected_sign}.png")
            if os.path.exists(img_path):
                st.image(img_path, caption=f"Sign Diagram: {selected_sign}", width=380)
            else:
                diag = engine.render_sign_image(selected_sign)
                st.image(diag, caption=f"Sign Diagram: {selected_sign}", width=380)

        with col_info:
            tamil_text, translit = BilingualTranslator.get_sign_tamil(selected_sign)
            vocab_info = BilingualTranslator.SIGN_VOCABULARY.get(selected_sign, {})

            st.markdown(f"### English Sign: **{selected_sign}**")
            st.markdown(f"### Tamil Meaning: <span class='tamil-tag'>{tamil_text}</span>", unsafe_allow_html=True)
            st.markdown(f"**Pronunciation (Transliteration):** *{translit}*")
            st.markdown(f"**Category:** {vocab_info.get('category', 'General')}")
            st.markdown(f"**Description:** {vocab_info.get('description', '')}")

            st.write("---")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"🔊 Speak in Tamil ({tamil_text})", key="spk_ta_samp"):
                    tts.speak(tamil_text, lang='ta')
                    st.success(f"Speaking: '{tamil_text}' in Tamil!")
            with c2:
                if st.button(f"🔊 Speak in English ({selected_sign})", key="spk_en_samp"):
                    tts.speak(selected_sign, lang='en')
                    st.success(f"Speaking: '{selected_sign}' in English!")

# -----------------------------------------------------------------------------
# 3. Text & Speech to Sign Language
# -----------------------------------------------------------------------------
elif sidebar_nav == "✍️ Text & Speech to Sign Language":
    st.header("✍️ Text / Speech to Sign Language Visual Translator")
    st.markdown("Translate written text or spoken words (in **English** or **Tamil**) into sequential visual Sign Language gestures:")

    sample_sentences = [
        "Custom Input",
        "வணக்கம் எனக்கு தண்ணீர் வேண்டும்",
        "வணக்கம் உதவி நன்றி",
        "Hello, thank you for your help",
        "I need water please",
        "Peace and love to everyone"
    ]

    selected_sample = st.selectbox("Choose a sample sentence or enter your own:", sample_sentences)

    if selected_sample == "Custom Input":
        input_text = st.text_input("Enter text (English or தமிழ்):", "வணக்கம் தண்ணீர் தயவுசெய்து")
    else:
        input_text = st.text_input("Enter text (English or தமிழ்):", selected_sample)

    tokens = engine.translate_text(input_text)

    if tokens:
        st.subheader("Step-by-Step Sign Sequence")
        st.write(f"Total Sign Steps: **{len(tokens)}**")

        # Display Sign Cards in an interactive carousel / grid
        cols = st.columns(min(len(tokens), 4))
        for idx, t in enumerate(tokens):
            with cols[idx % 4]:
                tok_name = t['token']
                tamil_t = t.get('tamil', '')
                translit_t = t.get('transliteration', '')
                typ = t.get('type', '')

                img_path = os.path.join(engine.assets_dir, f"{tok_name}.png")
                if os.path.exists(img_path):
                    st.image(img_path, caption=f"{idx+1}. [{typ.upper()}] {tok_name}\n{tamil_t} ({translit_t})", use_container_width=True)
                else:
                    gen_img = engine.render_sign_image(tok_name)
                    st.image(gen_img, caption=f"{idx+1}. [{typ.upper()}] {tok_name}\n{tamil_t} ({translit_t})", use_container_width=True)

        st.write("---")
        st.subheader("🔊 Audio Narration for Entire Sentence")
        col_aud1, col_aud2 = st.columns(2)

        with col_aud1:
            if st.button("🔊 Listen Entire Phrase in Tamil (தமிழ்)", key="listen_all_ta"):
                if BilingualTranslator.is_tamil_script(input_text):
                    ta_full = input_text
                else:
                    ta_full = BilingualTranslator.translate_sentence_to_tamil(input_text)
                tts.speak(ta_full, lang='ta')
                st.info(f"Speaking Tamil: \"{ta_full}\"")

        with col_aud2:
            if st.button("🔊 Listen Entire Phrase in English", key="listen_all_en"):
                en_full = input_text if not BilingualTranslator.is_tamil_script(input_text) else " ".join([t['token'] for t in tokens if t['token'] != 'SPACE'])
                tts.speak(en_full, lang='en')
                st.info(f"Speaking English: \"{en_full}\"")

# -----------------------------------------------------------------------------
# 4. Bilingual Sign Dictionary & Flashcards
# -----------------------------------------------------------------------------
elif sidebar_nav == "📖 Bilingual Sign Dictionary & Flashcards":
    st.header("📖 Bilingual Sign Dictionary (English & தமிழ்)")
    st.markdown("Complete visual reference dictionary with anatomical hand skeleton configurations and Tamil translations:")

    search_query = st.text_input("🔍 Search sign by English word, Tamil word, or category:", "")

    vocab_items = list(BilingualTranslator.SIGN_VOCABULARY.items())
    if search_query:
        q = search_query.lower()
        vocab_items = [
            (k, v) for k, v in vocab_items
            if q in k.lower() or q in v['tamil'] or q in v['transliteration'].lower() or q in v['category'].lower()
        ]

    for i in range(0, len(vocab_items), 3):
        row_items = vocab_items[i:i+3]
        cols = st.columns(len(row_items))
        for col, (sign_name, info) in zip(cols, row_items):
            with col:
                st.markdown(f"#### **{sign_name}**")
                st.markdown(f"**Tamil:** <span class='tamil-tag'>{info['tamil']}</span> *({info['transliteration']})*", unsafe_allow_html=True)
                st.caption(f"Category: {info['category']} | {info['description']}")

                img_path = os.path.join(engine.assets_dir, f"{sign_name}.png")
                if os.path.exists(img_path):
                    st.image(img_path, width=280)
                else:
                    diag = engine.render_sign_image(sign_name)
                    st.image(diag, width=280)

                if st.button(f"🔊 Speak {info['tamil']}", key=f"dict_btn_{sign_name}"):
                    tts.speak(info['tamil'], lang='ta')

# -----------------------------------------------------------------------------
# 5. Speech Synthesizer Studio
# -----------------------------------------------------------------------------
elif sidebar_nav == "🔊 Speech Synthesizer Studio":
    st.header("🔊 Bilingual Speech Synthesizer Studio")
    st.markdown("Test real-time Tamil and English speech synthesis engines:")

    col_ta, col_en = st.columns(2)

    with col_ta:
        st.subheader("🇮🇳 Tamil Speech Engine (Studio Voice)")
        ta_input = st.text_area("Tamil Text to Synthesize:", "வணக்கம்! நீங்கள் எப்படி இருக்கிறீர்கள்? உங்களுக்கு உதவி தேவையா?")
        if st.button("🔊 Play Tamil Audio (தமிழ்)", key="play_studio_ta"):
            tts.speak(ta_input, lang='ta')
            st.success(f"Synthesizing Tamil speech for: \"{ta_input}\"")

    with col_en:
        st.subheader("🇬🇧 English Speech Engine (Offline TTS)")
        en_input = st.text_area("English Text to Synthesize:", "Hello! How are you doing? Do you need any assistance?")
        rate = st.slider("Speech Rate (Words per minute):", min_value=100, max_value=240, value=160)
        if st.button("🔊 Play English Audio", key="play_studio_en"):
            tts.set_rate(rate)
            tts.speak(en_input, lang='en')
            st.success(f"Synthesizing English speech for: \"{en_input}\"")
