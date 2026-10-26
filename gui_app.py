"""
Bi-Directional Sign Language Assistive Hub (Tamil & English Desktop GUI)
Unified application supporting:
  1. Sign Language to Audio (Camera ➔ Hand Tracking ➔ English & Tamil Voice)
  2. Text & Voice to Sign Language (English & Tamil Text/Mic ➔ Sign Diagram Animations)
"""

import threading
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message=r".*SymbolDatabase\.GetPrototype.*")

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import cv2
import numpy as np
from PIL import Image, ImageTk

from src.hand_detector import HandDetector
from src.gesture_classifier import GestureClassifier
from src.sentence_builder import SentenceBuilder
from src.tts_engine import TTSEngine
from src.text_to_sign import TextToSignEngine
from src.translator import BilingualTranslator


class BiDirectionalSignApp(tk.Tk):
    """Unified desktop application for bilingual deaf and hearing communication."""

    def __init__(self):
        super().__init__()

        self.title("Bilingual Sign Language & Speech Assistive Suite (Tamil & English)")
        self.geometry("1220x860")
        self.minsize(1080, 750)
        self.configure(bg="#1a1c23")

        # Core logic components
        self.detector = HandDetector(max_hands=1, detection_con=0.7, track_con=0.5)
        self.classifier = GestureClassifier()
        self.sentence_builder = SentenceBuilder(hold_time_seconds=0.8, cooldown_seconds=0.6)
        self.tts = TTSEngine(rate=160, volume=1.0, default_lang="ta")
        self.t2s_engine = TextToSignEngine()

        # Tab 1 state
        self.cap = None
        self.is_camera_running = False
        self.auto_speak_var = tk.BooleanVar(value=False)
        self.active_audio_lang = tk.StringVar(value="ta")  # 'ta' or 'en'

        # Tab 2 state
        self.t2s_tokens = []
        self.t2s_current_index = 0
        self.t2s_is_playing = False
        self.t2s_speed = 0.9
        self.t2s_speak_audio = tk.BooleanVar(value=True)
        self.t2s_audio_lang = tk.StringVar(value="ta")

        # UI Construction
        self._configure_styles()
        self._build_header()
        self._build_tabbed_interface()
        self._build_status_bar()

        # Auto-start camera for Tab 1
        self.start_camera()

        # Load initial sign for Tab 2
        self.t2s_translate_and_load("Hello thank you")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _configure_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TNotebook", background="#1a1c23", borderwidth=0)
        style.configure("TNotebook.Tab", background="#262a36", foreground="#9aa0b4",
                        padding=[18, 9], font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TNotebook.Tab",
                  background=[("selected", "#00b4d8")],
                  foreground=[("selected", "#ffffff")])

    def _build_header(self):
        header = tk.Frame(self, bg="#20232c", height=68)
        header.pack(fill=tk.X, side=tk.TOP)

        title = tk.Label(
            header,
            text="🤟 BILINGUAL SIGN LANGUAGE ASSISTIVE SUITE",
            font=("Segoe UI", 16, "bold"),
            fg="#00e5ff",
            bg="#20232c"
        )
        title.pack(side=tk.LEFT, padx=20, pady=12)

        subtitle = tk.Label(
            header,
            text="Two-Way Inclusive Communication: Sign ➔ Tamil/English Speech  |  Text ➔ Visual Sign",
            font=("Segoe UI", 10, "italic"),
            fg="#8d99ae",
            bg="#20232c"
        )
        subtitle.pack(side=tk.LEFT, padx=5, pady=12)

    def _build_tabbed_interface(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Tab 1: Sign Language to Audio
        self.tab_s2a = tk.Frame(self.notebook, bg="#1a1c23")
        self.notebook.add(self.tab_s2a, text=" 📹 1. Sign Language ➔ Audio (Tamil & English) ")
        self._build_tab1_sign_to_audio(self.tab_s2a)

        # Tab 2: Text/Voice to Sign Language
        self.tab_t2s = tk.Frame(self.notebook, bg="#1a1c23")
        self.notebook.add(self.tab_t2s, text=" ✍️ 2. Text / Voice ➔ Sign Language ")
        self._build_tab2_text_to_sign(self.tab_t2s)

    # -------------------------------------------------------------------------
    # TAB 1: Sign Language to Audio
    # -------------------------------------------------------------------------
    def _build_tab1_sign_to_audio(self, parent):
        container = tk.Frame(parent, bg="#1a1c23")
        container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Left Column: Video Feed
        video_col = tk.Frame(container, bg="#1a1c23")
        video_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        video_frame = tk.LabelFrame(video_col, text=" Live Camera Feed & Landmark Tracking ",
                                    fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"))
        video_frame.pack(fill=tk.BOTH, expand=True)

        self.video_canvas = tk.Label(video_frame, bg="#0d0e12")
        self.video_canvas.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Camera Controls underneath video
        cam_ctrl = tk.Frame(video_col, bg="#20232c", height=45)
        cam_ctrl.pack(fill=tk.X, pady=(6, 0))

        self.btn_cam_toggle = tk.Button(
            cam_ctrl, text="⏸ Pause Camera", font=("Segoe UI", 9, "bold"),
            bg="#2b3040", fg="#ffffff", activebackground="#3d445c",
            command=self.toggle_camera, width=15
        )
        self.btn_cam_toggle.pack(side=tk.LEFT, padx=10, pady=8)

        chk_auto = tk.Checkbutton(
            cam_ctrl, text="Auto-Speak on Sign Confirmation",
            variable=self.auto_speak_var, bg="#20232c", fg="#e0e0e0",
            selectcolor="#1a1c23", activebackground="#20232c",
            font=("Segoe UI", 9)
        )
        chk_auto.pack(side=tk.LEFT, padx=10)

        # Right Column: Dashboard Controls
        control_col = tk.Frame(container, bg="#1a1c23", width=460)
        control_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        control_col.pack_propagate(False)

        # Gesture Detection Card
        card_gesture = tk.LabelFrame(control_col, text=" Real-Time Gesture Detection ",
                                     fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"))
        card_gesture.pack(fill=tk.X, pady=(0, 8))

        f_det = tk.Frame(card_gesture, bg="#20232c")
        f_det.pack(fill=tk.X, padx=12, pady=6)

        self.lbl_sign_name = tk.Label(f_det, text="NONE", font=("Segoe UI", 20, "bold"),
                                      fg="#38ef7d", bg="#20232c")
        self.lbl_sign_name.pack(anchor="w")

        self.lbl_sign_tamil = tk.Label(f_det, text="தமிழ்: -", font=("Segoe UI", 12, "bold"),
                                       fg="#00e5ff", bg="#20232c")
        self.lbl_sign_tamil.pack(anchor="w", pady=(2, 0))

        self.lbl_sign_meta = tk.Label(f_det, text="Confidence: 0% | Source: Idle",
                                      font=("Segoe UI", 9), fg="#8d99ae", bg="#20232c")
        self.lbl_sign_meta.pack(anchor="w", pady=(2, 2))

        self.lbl_ml_probs = tk.Label(f_det, text="ML Model (41 classes): Active",
                                     font=("Segoe UI", 8, "italic"), fg="#00b4d8", bg="#20232c")
        self.lbl_ml_probs.pack(anchor="w", pady=(0, 6))

        tk.Label(f_det, text="Hold-to-Confirm Stabilization:", font=("Segoe UI", 8),
                 fg="#adb5bd", bg="#20232c").pack(anchor="w")

        self.prog_hold = ttk.Progressbar(f_det, orient="horizontal", mode="determinate", length=380)
        self.prog_hold.pack(fill=tk.X, pady=(2, 6))

        # Sentence Builder Card (English & Tamil)
        card_sentence = tk.LabelFrame(control_col, text=" Sentence Builder & Translation ",
                                      fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"))
        card_sentence.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

        f_sent = tk.Frame(card_sentence, bg="#20232c")
        f_sent.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        tk.Label(f_sent, text="English Sentence:", font=("Segoe UI", 9, "bold"),
                 fg="#00b4d8", bg="#20232c").pack(anchor="w")
        self.txt_sentence_en = tk.Text(f_sent, height=2, font=("Segoe UI", 11),
                                       bg="#14161d", fg="#ffffff", wrap=tk.WORD, borderwidth=1)
        self.txt_sentence_en.pack(fill=tk.X, pady=(2, 8))

        tk.Label(f_sent, text="Tamil Translation (தமிழ் மொழிபெயர்ப்பு):", font=("Segoe UI", 9, "bold"),
                 fg="#00e676", bg="#20232c").pack(anchor="w")
        self.txt_sentence_ta = tk.Text(f_sent, height=2, font=("Segoe UI", 11),
                                       bg="#14161d", fg="#00e676", wrap=tk.WORD, borderwidth=1)
        self.txt_sentence_ta.pack(fill=tk.X, pady=(2, 8))

        # Action Buttons
        f_actions = tk.Frame(f_sent, bg="#20232c")
        f_actions.pack(fill=tk.X, pady=(4, 6))

        btn_speak_ta = tk.Button(
            f_actions, text="🔊 தமிழ் குரல் (Tamil)", font=("Segoe UI", 9, "bold"),
            bg="#00b4d8", fg="#ffffff", activebackground="#0096c7",
            command=self.speak_tamil_sentence
        )
        btn_speak_ta.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        btn_speak_en = tk.Button(
            f_actions, text="🔊 Speak English", font=("Segoe UI", 9, "bold"),
            bg="#11998e", fg="#ffffff", activebackground="#38ef7d",
            command=self.speak_english_sentence
        )
        btn_speak_en.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # Buffer Modifiers
        f_mods = tk.Frame(f_sent, bg="#20232c")
        f_mods.pack(fill=tk.X, pady=(4, 0))

        tk.Button(f_mods, text="␣ Space", font=("Segoe UI", 8), bg="#2b3040", fg="#ffffff",
                  command=self.action_space, width=8).pack(side=tk.LEFT, padx=(0, 4))
        tk.Button(f_mods, text="⌫ Delete", font=("Segoe UI", 8), bg="#2b3040", fg="#ffffff",
                  command=self.action_backspace, width=8).pack(side=tk.LEFT, padx=4)
        tk.Button(f_mods, text="🗑 Clear", font=("Segoe UI", 8), bg="#d90429", fg="#ffffff",
                  command=self.action_clear, width=8).pack(side=tk.LEFT, padx=4)

        # Recent Speech Log
        card_log = tk.LabelFrame(control_col, text=" Spoken Utterance Log ",
                                 fg="#00e5ff", bg="#20232c", font=("Segoe UI", 9, "bold"))
        card_log.pack(fill=tk.X)
        self.txt_log = scrolledtext.ScrolledText(card_log, height=3, font=("Segoe UI", 8),
                                                bg="#14161d", fg="#adb5bd")
        self.txt_log.pack(fill=tk.BOTH, padx=8, pady=6)

    # -------------------------------------------------------------------------
    # TAB 2: Text / Voice to Sign Language
    # -------------------------------------------------------------------------
    def _build_tab2_text_to_sign(self, parent):
        container = tk.Frame(parent, bg="#1a1c23")
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Input Bar across top
        input_card = tk.LabelFrame(container, text=" Input Text (English or தமிழ்) or Microphone Voice ",
                                   fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"))
        input_card.pack(fill=tk.X, pady=(0, 10))

        f_in = tk.Frame(input_card, bg="#20232c")
        f_in.pack(fill=tk.X, padx=12, pady=8)

        self.t2s_entry = tk.Entry(f_in, font=("Segoe UI", 12), bg="#14161d", fg="#ffffff",
                                  insertbackground="#ffffff", borderwidth=2)
        self.t2s_entry.insert(0, "வணக்கம் எனக்கு தண்ணீர் வேண்டும்")
        self.t2s_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.t2s_entry.bind("<Return>", lambda e: self.t2s_on_translate_click())

        btn_translate = tk.Button(
            f_in, text="✨ Translate to Sign", font=("Segoe UI", 10, "bold"),
            bg="#00b4d8", fg="#ffffff", activebackground="#0096c7",
            command=self.t2s_on_translate_click, padx=12
        )
        btn_translate.pack(side=tk.LEFT, padx=4)

        self.btn_mic_ta = tk.Button(
            f_in, text="🎙️ தமிழ் Mic", font=("Segoe UI", 9, "bold"),
            bg="#7209b7", fg="#ffffff", activebackground="#560bad",
            command=lambda: self.t2s_mic_input(lang='ta-IN'), padx=10
        )
        self.btn_mic_ta.pack(side=tk.LEFT, padx=4)

        self.btn_mic_en = tk.Button(
            f_in, text="🎙️ English Mic", font=("Segoe UI", 9, "bold"),
            bg="#4361ee", fg="#ffffff", activebackground="#3a0ca3",
            command=lambda: self.t2s_mic_input(lang='en-US'), padx=10
        )
        self.btn_mic_en.pack(side=tk.LEFT, padx=4)


        # Middle Content: Sign Display Card (Left) + Timeline / Steps (Right)
        f_mid = tk.Frame(container, bg="#1a1c23")
        f_mid.pack(fill=tk.BOTH, expand=True)

        # Visual Card Display
        card_display = tk.LabelFrame(f_mid, text=" Visual Sign Language Gesture Animation ",
                                     fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"))
        card_display.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))

        self.t2s_canvas = tk.Label(card_display, bg="#0d0e12")
        self.t2s_canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Sign metadata overlay beneath canvas
        f_card_meta = tk.Frame(card_display, bg="#20232c")
        f_card_meta.pack(fill=tk.X, padx=12, pady=(0, 8))

        self.lbl_t2s_sign_name = tk.Label(f_card_meta, text="SIGN: -", font=("Segoe UI", 14, "bold"),
                                          fg="#00e5ff", bg="#20232c")
        self.lbl_t2s_sign_name.pack(side=tk.LEFT)

        self.lbl_t2s_tamil_name = tk.Label(f_card_meta, text="தமிழ்: -", font=("Segoe UI", 12, "bold"),
                                           fg="#00e676", bg="#20232c")
        self.lbl_t2s_tamil_name.pack(side=tk.LEFT, padx=15)

        self.lbl_t2s_desc = tk.Label(f_card_meta, text="Description: -", font=("Segoe UI", 9),
                                     fg="#8d99ae", bg="#20232c")
        self.lbl_t2s_desc.pack(side=tk.RIGHT)

        # Playback Controls underneath canvas
        f_ctrl = tk.Frame(card_display, bg="#1a1c23")
        f_ctrl.pack(fill=tk.X, padx=8, pady=(0, 8))

        tk.Button(f_ctrl, text="⏮ Prev", font=("Segoe UI", 9, "bold"), bg="#2b3040", fg="#ffffff",
                  command=self.t2s_prev, width=8).pack(side=tk.LEFT, padx=4)

        self.btn_t2s_play = tk.Button(f_ctrl, text="▶ Play", font=("Segoe UI", 9, "bold"),
                                      bg="#00b4d8", fg="#ffffff", command=self.t2s_toggle_play, width=10)
        self.btn_t2s_play.pack(side=tk.LEFT, padx=4)

        tk.Button(f_ctrl, text="⏭ Next", font=("Segoe UI", 9, "bold"), bg="#2b3040", fg="#ffffff",
                  command=self.t2s_next, width=8).pack(side=tk.LEFT, padx=4)

        tk.Label(f_ctrl, text="Speed:", font=("Segoe UI", 9), fg="#e0e0e0", bg="#1a1c23").pack(side=tk.LEFT, padx=(15, 4))
        self.speed_slider = tk.Scale(f_ctrl, from_=0.3, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
                                     bg="#1a1c23", fg="#ffffff", highlightthickness=0, length=120,
                                     command=self.t2s_update_speed)
        self.speed_slider.set(0.9)
        self.speed_slider.pack(side=tk.LEFT, padx=4)

        chk_t2s_audio = tk.Checkbutton(
            f_ctrl, text="Speak audio on each step", variable=self.t2s_speak_audio,
            bg="#1a1c23", fg="#e0e0e0", selectcolor="#20232c", font=("Segoe UI", 9)
        )
        chk_t2s_audio.pack(side=tk.RIGHT, padx=10)

        # Right Panel: Sign Timeline / Sequence List
        card_timeline = tk.LabelFrame(f_mid, text=" Sign Sequence & Steps ",
                                      fg="#00e5ff", bg="#20232c", font=("Segoe UI", 10, "bold"), width=340)
        card_timeline.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(0, 0))
        card_timeline.pack_propagate(False)

        self.listbox_timeline = tk.Listbox(card_timeline, font=("Segoe UI", 10), bg="#14161d",
                                           fg="#ffffff", selectbackground="#00b4d8",
                                           selectforeground="#ffffff", borderwidth=0)
        self.listbox_timeline.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.listbox_timeline.bind("<<ListboxSelect>>", self.t2s_on_listbox_select)

    def _build_status_bar(self):
        self.status_bar = tk.Label(self, text=" System Ready | Models & Audio Initialized ",
                                   font=("Segoe UI", 8), bg="#0f1117", fg="#6c757d",
                                   anchor="w", padx=10, pady=4)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    # -------------------------------------------------------------------------
    # Tab 1 Logic: Camera & Gesture Processing
    # -------------------------------------------------------------------------
    def start_camera(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.is_camera_running = True
        self.btn_cam_toggle.config(text="⏸ Pause Camera", bg="#2b3040")
        self._camera_loop()

    def stop_camera(self):
        self.is_camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.btn_cam_toggle.config(text="▶ Resume Camera", bg="#00b4d8")

    def toggle_camera(self):
        if self.is_camera_running:
            self.stop_camera()
        else:
            self.start_camera()

    def _camera_loop(self):
        if not self.is_camera_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            processed, lm_list, bbox = self.detector.find_landmarks(frame, draw=True)

            if lm_list:
                norm_feat = self.detector.get_normalized_landmarks(lm_list)
                hand_type = self.detector.get_hand_type(processed)
                label, conf, src = self.classifier.classify(norm_feat, lm_list, hand_type)

                confirmed, progress, in_cool = self.sentence_builder.update(label, conf)
                self.prog_hold['value'] = progress * 100

                # Fetch Tamil translation
                tamil_word, translit = BilingualTranslator.get_sign_tamil(label)

                self.lbl_sign_name.config(text=label, fg="#38ef7d" if label != "UNKNOWN" else "#8d99ae")
                self.lbl_sign_tamil.config(text=f"தமிழ்: {tamil_word} ({translit})")
                self.lbl_sign_meta.config(text=f"Confidence: {int(conf * 100)}% | Engine: {src}")

                # Display real-time ML Top-3 class probabilities
                top_cands = getattr(self.classifier, 'last_top_candidates', [])
                if top_cands:
                    top_str = " | ".join([f"{c} ({int(p*100)}%)" for c, p in top_cands[:3]])
                    self.lbl_ml_probs.config(text=f"ML Top-3: {top_str}", fg="#00d2ff")

                if confirmed:
                    # Update sentence buffer UI
                    self.update_sentence_display()
                    if self.auto_speak_var.get():
                        if self.active_audio_lang.get() == "ta":
                            t_text, _ = BilingualTranslator.get_sign_tamil(confirmed)
                            self.tts.speak(t_text, lang='ta')
                        else:
                            self.tts.speak(confirmed, lang='en')
            else:
                self.sentence_builder.update("UNKNOWN", 0.0)
                self.prog_hold['value'] = 0
                self.lbl_sign_name.config(text="NONE", fg="#8d99ae")
                self.lbl_sign_tamil.config(text="தமிழ்: -")
                self.lbl_sign_meta.config(text="Waiting for gesture... (Sentence preserved)", fg="#8d99ae")
                self.lbl_ml_probs.config(text="ML Model (41 classes): Ready for input", fg="#6c757d")


            # Render video frame to Tkinter Canvas
            img_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            self.video_canvas.imgtk = img_tk
            self.video_canvas.configure(image=img_tk)
        else:
            # Fallback placeholder if camera is initializing or not connected
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(placeholder, "Connecting to camera / Standby...", (80, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 200, 255), 2)
            img_rgb = cv2.cvtColor(placeholder, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            img_tk = ImageTk.PhotoImage(image=img_pil)
            self.video_canvas.imgtk = img_tk
            self.video_canvas.configure(image=img_tk)

        self.after(30, self._camera_loop)


    def update_sentence_display(self):
        en_sentence = self.sentence_builder.sentence
        self.txt_sentence_en.delete("1.0", tk.END)
        self.txt_sentence_en.insert(tk.END, en_sentence)

        ta_sentence = self.sentence_builder.get_tamil_translation()
        self.txt_sentence_ta.delete("1.0", tk.END)
        self.txt_sentence_ta.insert(tk.END, ta_sentence)

    def speak_tamil_sentence(self):
        ta_sentence = self.txt_sentence_ta.get("1.0", tk.END).strip()
        if not ta_sentence:
            ta_sentence = self.sentence_builder.get_tamil_translation()
        if ta_sentence:
            self.tts.speak(ta_sentence, lang='ta')
            self._log_speech(f"[Tamil Voice] {ta_sentence}")

    def speak_english_sentence(self):
        en_sentence = self.txt_sentence_en.get("1.0", tk.END).strip()
        if en_sentence:
            self.tts.speak(en_sentence, lang='en')
            self._log_speech(f"[English Voice] {en_sentence}")

    def action_space(self):
        self.sentence_builder.add_space()
        self.update_sentence_display()

    def action_backspace(self):
        self.sentence_builder.backspace()
        self.update_sentence_display()

    def action_clear(self):
        self.sentence_builder.clear()
        self.update_sentence_display()

    def _log_speech(self, text: str):
        t_str = time.strftime("%H:%M:%S")
        self.txt_log.insert(tk.END, f"[{t_str}] {text}\n")
        self.txt_log.see(tk.END)

    # -------------------------------------------------------------------------
    # Tab 2 Logic: Text to Sign Language
    # -------------------------------------------------------------------------
    def t2s_on_translate_click(self):
        raw_text = self.t2s_entry.get().strip()
        if raw_text:
            self.t2s_translate_and_load(raw_text)

    def t2s_mic_input(self, lang: str = 'ta-IN'):
        target_btn = self.btn_mic_ta if lang == 'ta-IN' else self.btn_mic_en
        orig_text = target_btn.cget("text")
        orig_bg = target_btn.cget("bg")

        target_btn.config(text="🔴 Listening...", bg="#e63946")
        lang_label = "Tamil (தமிழ்)" if lang == 'ta-IN' else "English"
        self.status_bar.config(text=f" 🎙️ Listening in {lang_label}... Speak into your microphone now! ", fg="#ffb703")
        self.update()

        def _record():
            try:
                recognized = self.t2s_engine.speech_to_text(language=lang)
                if recognized and not recognized.startswith("["):
                    self.t2s_entry.delete(0, tk.END)
                    self.t2s_entry.insert(0, recognized)
                    self.t2s_translate_and_load(recognized)
                    self.status_bar.config(text=f" 🎙️ Transcribed ({lang_label}): \"{recognized}\"", fg="#38ef7d")
                else:
                    # Isolated failure: do NOT touch existing output or clear current signs
                    warning_msg = recognized if recognized else "No speech detected."
                    self.status_bar.config(
                        text=f" ⚠️ Voice attempt: {warning_msg} (Previous text & signs preserved)",
                        fg="#ffb703"
                    )
            except Exception as e:
                self.status_bar.config(text=f" ⚠️ Microphone error: {e} (Previous output preserved)", fg="#ffb703")
            finally:
                target_btn.config(text=orig_text, bg=orig_bg)

        threading.Thread(target=_record, daemon=True).start()


    def t2s_translate_and_load(self, text: str):
        new_tokens = self.t2s_engine.translate_text(text)
        if not new_tokens:
            # Isolated failure: keep existing output intact
            self.status_bar.config(text=f" ⚠️ Could not translate '{text}' to signs. Existing output preserved.", fg="#ffb703")
            return

        self.t2s_tokens = new_tokens
        self.t2s_current_index = 0
        self.t2s_is_playing = False
        self.btn_t2s_play.config(text="▶ Play", bg="#00b4d8")

        # Populate timeline listbox
        self.listbox_timeline.delete(0, tk.END)
        for idx, item in enumerate(self.t2s_tokens):
            tok = item['token']
            typ = item['type'].upper()
            tam = item.get('tamil', '')
            trans = item.get('transliteration', '')
            display_str = f" {idx+1}. [{typ}] {tok} ➔ {tam} ({trans})"
            self.listbox_timeline.insert(tk.END, display_str)

        if self.t2s_tokens:
            self.t2s_display_current_sign()


    def t2s_display_current_sign(self):
        if not self.t2s_tokens or self.t2s_current_index >= len(self.t2s_tokens):
            return

        item = self.t2s_tokens[self.t2s_current_index]
        token_name = item['token']
        tamil_name = item.get('tamil', '')
        translit = item.get('transliteration', '')
        desc = item.get('description', '')

        # Update metadata labels
        self.lbl_t2s_sign_name.config(text=f"SIGN: {token_name}")
        self.lbl_t2s_tamil_name.config(text=f"தமிழ்: {tamil_name} ({translit})")
        self.lbl_t2s_desc.config(text=f"Description: {desc}")

        # Highlight in timeline listbox
        self.listbox_timeline.selection_clear(0, tk.END)
        self.listbox_timeline.selection_set(self.t2s_current_index)
        self.listbox_timeline.see(self.t2s_current_index)

        # Render visual diagram
        img_bgr = self.t2s_engine.render_sign_image(token_name, width=640, height=480)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)
        self.t2s_canvas.imgtk = img_tk
        self.t2s_canvas.configure(image=img_tk)

        # Spoken audio accompaniment
        if self.t2s_speak_audio.get() and token_name != 'SPACE':
            if self.t2s_audio_lang.get() == "ta":
                self.tts.speak(tamil_name, lang='ta')
            else:
                self.tts.speak(token_name, lang='en')

    def t2s_next(self):
        if self.t2s_tokens:
            self.t2s_current_index = (self.t2s_current_index + 1) % len(self.t2s_tokens)
            self.t2s_display_current_sign()

    def t2s_prev(self):
        if self.t2s_tokens:
            self.t2s_current_index = (self.t2s_current_index - 1) % len(self.t2s_tokens)
            self.t2s_display_current_sign()

    def t2s_toggle_play(self):
        if self.t2s_is_playing:
            self.t2s_is_playing = False
            self.btn_t2s_play.config(text="▶ Play", bg="#00b4d8")
        else:
            self.t2s_is_playing = True
            self.btn_t2s_play.config(text="⏸ Pause", bg="#d90429")
            self._t2s_play_loop()

    def _t2s_play_loop(self):
        if not self.t2s_is_playing or not self.t2s_tokens:
            return

        self.t2s_display_current_sign()

        # Advance index
        if self.t2s_current_index < len(self.t2s_tokens) - 1:
            self.t2s_current_index += 1
            delay_ms = int(self.t2s_speed * 1000)
            self.after(delay_ms, self._t2s_play_loop)
        else:
            # Reached end
            self.t2s_is_playing = False
            self.btn_t2s_play.config(text="▶ Replay", bg="#00b4d8")

    def t2s_update_speed(self, val):
        self.t2s_speed = float(val)

    def t2s_on_listbox_select(self, event):
        sel = self.listbox_timeline.curselection()
        if sel:
            self.t2s_current_index = sel[0]
            self.t2s_display_current_sign()

    def on_close(self):
        self.stop_camera()
        self.tts.stop()
        self.destroy()


if __name__ == "__main__":
    app = BiDirectionalSignApp()
    app.mainloop()
