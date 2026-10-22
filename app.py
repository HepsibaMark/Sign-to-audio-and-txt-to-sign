"""
Sign Language to Audio - Bilingual OpenCV HUD Application (Tamil & English)
Real-time webcam gesture detection, sentence building, bilingual translation,
and dual-language speech synthesis.
"""

import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message=r".*SymbolDatabase\.GetPrototype.*")

import cv2
import numpy as np
from src.hand_detector import HandDetector
from src.gesture_classifier import GestureClassifier
from src.sentence_builder import SentenceBuilder
from src.tts_engine import TTSEngine
from src.translator import BilingualTranslator


def draw_hud(img: np.ndarray,
             current_sign: str,
             confidence: float,
             source: str,
             hold_progress: float,
             sentence: str,
             tamil_translit: str,
             is_speaking: bool,
             auto_speak: bool,
             active_lang: str,
             fps: float):
    """Draws an informative, modern bilingual HUD overlay on the video feed."""
    h, w, _ = img.shape

    # 1. Top Header Banner
    header_h = 55
    overlay = img.copy()
    cv2.rectangle(overlay, (0, 0), (w, header_h), (25, 25, 25), -1)
    cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

    # Title
    cv2.putText(img, "SIGN LANGUAGE TO AUDIO (TAMIL & ENGLISH)", (20, 36),
                cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 240, 255), 2)

    # Active Language indicator
    lang_display = "VOICE: TAMIL (தமிழ்)" if active_lang == 'ta' else "VOICE: ENGLISH"
    lang_color = (0, 220, 255) if active_lang == 'ta' else (0, 255, 120)
    cv2.putText(img, f"[{lang_display} - Press L to Switch]", (w - 530, 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, lang_color, 1)

    # Auto-speak mode & FPS
    mode_str = "AUTO: ON" if auto_speak else "AUTO: OFF"
    cv2.putText(img, mode_str, (w - 200, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 255, 180) if auto_speak else (180, 180, 180), 1)
    cv2.putText(img, f"FPS: {fps:.1f}", (w - 95, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.50, (200, 200, 200), 1)

    # 2. Left Gesture Card (Detection & Confidence)
    card_w = 320
    card_h = 145
    cx, cy = 20, 75
    cv2.rectangle(img, (cx, cy), (cx + card_w, cy + card_h), (20, 20, 20), -1)
    cv2.rectangle(img, (cx, cy), (cx + card_w, cy + card_h), (60, 60, 60), 1)

    cv2.putText(img, "DETECTED GESTURE", (cx + 15, cy + 24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Sign label & Tamil transliteration
    sign_color = (0, 255, 0) if current_sign != "UNKNOWN" else (100, 100, 100)
    cv2.putText(img, current_sign, (cx + 15, cy + 58),
                cv2.FONT_HERSHEY_DUPLEX, 0.85, sign_color, 2)

    # Tamil meaning in Roman transliteration (for reliable OpenCV rendering)
    if current_sign != "UNKNOWN":
        _, translit = BilingualTranslator.get_sign_tamil(current_sign)
        cv2.putText(img, f"Tamil: {translit}", (cx + 15, cy + 82),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0, 220, 255), 1)

    # Confidence & Source
    conf_pct = int(confidence * 100)
    cv2.putText(img, f"Conf: {conf_pct}% ({source})", (cx + 15, cy + 106),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)

    # Hold Progress Bar
    bar_x, bar_y = cx + 15, cy + 120
    bar_max_w = card_w - 30
    bar_fill_w = int(hold_progress * bar_max_w)
    cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_max_w, bar_y + 12), (50, 50, 50), -1)
    if bar_fill_w > 0:
        cv2.rectangle(img, (bar_x, bar_y), (bar_x + bar_fill_w, bar_y + 12), (0, 220, 255), -1)

    # 3. Bottom Sentence & Audio Dashboard
    bottom_h = 135
    by = h - bottom_h
    overlay2 = img.copy()
    cv2.rectangle(overlay2, (0, by), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay2, 0.90, img, 0.10, 0, img)

    # Audio synthesis indicator
    audio_icon_color = (0, 255, 0) if is_speaking else (120, 120, 120)
    audio_text = f"[SPEAKING ({active_lang.upper()})...]" if is_speaking else f"[AUDIO READY ({active_lang.upper()})]"
    cv2.circle(img, (30, by + 24), 7, audio_icon_color, -1)
    cv2.putText(img, audio_text, (48, by + 29),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, audio_icon_color, 2)

    # Sentence Banner (English)
    display_sent = sentence if sentence else "(Hold gesture to build sentence...)"
    sent_color = (255, 255, 255) if sentence else (140, 140, 140)
    cv2.putText(img, "ENGLISH:", (30, by + 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 2)
    cv2.putText(img, f'"{display_sent}"', (130, by + 58),
                cv2.FONT_HERSHEY_DUPLEX, 0.65, sent_color, 2)

    # Tamil Translation Banner
    tamil_disp = tamil_translit if tamil_translit else "(Tamil translation will appear here...)"
    cv2.putText(img, "TAMIL:", (30, by + 88),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 160), 2)
    cv2.putText(img, f'"{tamil_disp}"', (130, by + 88),
                cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 255, 180) if sentence else (140, 140, 140), 2)

    # Hotkey guide
    cv2.putText(img, "[E] Speak English  |  [T] Speak Tamil  |  [L] Toggle Voice  |  [SPACE]  |  [BKSP]  |  [C] Clear  |  [Q] Exit",
                (30, by + 118), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (180, 180, 180), 1)

    return img


def run_app():
    print("=" * 65)
    print("  BILINGUAL SIGN LANGUAGE TO AUDIO (TAMIL & ENGLISH)")
    print("=" * 65)

    # Initialize modules
    print("[System] Initializing Hand Detector (MediaPipe)...")
    detector = HandDetector(max_hands=1, detection_con=0.7, track_con=0.5)

    print("[System] Initializing Gesture Classifier...")
    classifier = GestureClassifier()

    print("[System] Initializing Sentence Builder...")
    sentence_builder = SentenceBuilder(hold_time_seconds=0.8, cooldown_seconds=0.6)

    print("[System] Initializing Bilingual Text-to-Speech Engine...")
    tts = TTSEngine(rate=160, volume=1.0, default_lang="ta")
    tts.speak("Sign language to audio system is ready.", lang="en")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[Error] Could not access webcam. Ensure a camera is connected.")
        return

    # Set camera resolution
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    prev_time = time.time()
    auto_speak = False
    active_lang = "ta"  # Default to Tamil voice
    current_sign = "UNKNOWN"
    current_conf = 0.0
    current_source = "None"
    hold_progress = 0.0

    print("\n[Application Running] Press 'Q' in the video window to quit.")
    print("  - Press 'E' to speak in English")
    print("  - Press 'T' to speak in Tamil (தமிழ்)")
    print("  - Press 'L' to toggle default speech language")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Warning] Failed to grab frame from camera.")
            break

        # Flip horizontally for natural mirror interaction
        frame = cv2.flip(frame, 1)

        # FPS computation
        now = time.time()
        fps = 1.0 / (now - prev_time) if (now - prev_time) > 0 else 30.0
        prev_time = now

        # Hand detection & landmark extraction
        processed_frame, lm_list, bbox = detector.find_landmarks(frame, draw=True)

        if lm_list:
            norm_features = detector.get_normalized_landmarks(lm_list)
            hand_type = detector.get_hand_type(processed_frame)

            # Classify gesture
            predicted_label, conf, source = classifier.classify(norm_features, lm_list, hand_type)

            current_sign = predicted_label
            current_conf = conf
            current_source = source

            # Stabilize and register sign in sentence builder
            confirmed_token, progress, in_cooldown = sentence_builder.update(predicted_label, conf)
            hold_progress = progress

            if confirmed_token is not None:
                print(f"[Registered] '{confirmed_token}' (Hold Complete)")
                if auto_speak:
                    if active_lang == 'ta':
                        tamil_text, _ = BilingualTranslator.get_sign_tamil(confirmed_token)
                        tts.speak(tamil_text, lang='ta')
                    else:
                        tts.speak(confirmed_token, lang='en')
        else:
            current_sign = "UNKNOWN"
            current_conf = 0.0
            current_source = "None"
            hold_progress = 0.0
            sentence_builder.update("UNKNOWN", 0.0)

        # Compute Tamil translation for the current sentence
        current_sentence = sentence_builder.sentence
        tamil_translit = ""
        tamil_script = ""
        if current_sentence.strip():
            tamil_script = sentence_builder.get_tamil_translation()
            # For HUD, transliterate Tamil script into Latin characters for clean OpenCV font rendering
            tamil_translit = BilingualTranslator.transliterate_tamil_to_latin(tamil_script)

        # Render Bilingual HUD
        hud_frame = draw_hud(
            img=processed_frame,
            current_sign=current_sign,
            confidence=current_conf,
            source=current_source,
            hold_progress=hold_progress,
            sentence=current_sentence,
            tamil_translit=tamil_translit,
            is_speaking=tts.is_speaking,
            auto_speak=auto_speak,
            active_lang=active_lang,
            fps=fps
        )

        cv2.imshow("Sign Language to Audio (Tamil & English)", hud_frame)

        key = cv2.waitKey(1) & 0xFF

        # [Q] Quit
        if key == ord('q') or key == ord('Q') or key == 27:
            break

        # [E] Speak in English
        elif key == ord('e') or key == ord('E'):
            text = sentence_builder.sentence.strip()
            if text:
                print(f"[TTS-EN] Speaking: \"{text}\"")
                tts.speak(text, lang='en')

        # [T] Speak in Tamil
        elif key == ord('t') or key == ord('T'):
            text = sentence_builder.sentence.strip()
            if text:
                tamil_text = sentence_builder.get_tamil_translation()
                print(f"[TTS-TA] Speaking Tamil: \"{tamil_text}\"")
                tts.speak(tamil_text, lang='ta')

        # [ENTER] or [S] Speak in active language
        elif key == 13 or key == ord('s') or key == ord('S'):
            text = sentence_builder.sentence.strip()
            if text:
                if active_lang == 'ta':
                    tamil_text = sentence_builder.get_tamil_translation()
                    print(f"[TTS-TA] Speaking Tamil: \"{tamil_text}\"")
                    tts.speak(tamil_text, lang='ta')
                else:
                    print(f"[TTS-EN] Speaking English: \"{text}\"")
                    tts.speak(text, lang='en')

        # [L] Toggle default language
        elif key == ord('l') or key == ord('L'):
            active_lang = 'en' if active_lang == 'ta' else 'ta'
            tts.set_default_language(active_lang)
            print(f"[Language] Switched active speech language to: {active_lang.upper()}")

        # [SPACE] Insert space
        elif key == 32:
            sentence_builder.add_space()

        # [BACKSPACE]
        elif key == 8:
            sentence_builder.backspace()

        # [C] Clear
        elif key == ord('c') or key == ord('C'):
            sentence_builder.clear()
            print("[Sentence] Cleared.")

        # [M] Toggle auto-speak
        elif key == ord('m') or key == ord('M'):
            auto_speak = not auto_speak
            print(f"[Auto-Speak] Toggled to: {auto_speak}")

    # Clean release
    cap.release()
    cv2.destroyAllWindows()
    tts.stop()
    print("[System] Application gracefully shut down.")


if __name__ == "__main__":
    run_app()
