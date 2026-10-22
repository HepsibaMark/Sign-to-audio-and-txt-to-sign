"""
Text & Voice to Sign Language (T2SL) - Bilingual Visual Player Application
Translates written text or microphone speech (Tamil & English) into sequential
Sign Language gestures with real-time animated playback and visual landmark diagrams.
"""

import os
import threading
import time
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="google.protobuf")
warnings.filterwarnings("ignore", message=r".*SymbolDatabase\.GetPrototype.*")

import tkinter as tk
from tkinter import ttk, messagebox
import cv2
from PIL import Image, ImageTk

from src.text_to_sign import TextToSignEngine
from src.tts_engine import TTSEngine
from src.translator import BilingualTranslator


class TextToSignApp(tk.Tk):
    """Desktop player for translating Text or Voice (Tamil & English) into Sign Language."""

    def __init__(self):
        super().__init__()

        self.title("Text & Voice to Sign Language - Bilingual Visual Translator (Tamil & English)")
        self.geometry("1120x820")
        self.minsize(980, 720)
        self.configure(bg="#1a1c23")

        self.engine = TextToSignEngine()
        self.tts = TTSEngine(rate=160, volume=1.0, default_lang="ta")

        # State management
        self.tokens = []
        self.current_index = 0
        self.is_playing = False
        self.playback_speed = 0.9  # seconds per sign
        self.speak_while_signing = tk.BooleanVar(value=True)
        self.audio_lang_var = tk.StringVar(value="ta")  # 'ta' or 'en'

        self._build_header()
        self._build_input_panel()
        self._build_player_panel()
        self._build_timeline_panel()

        # Set default welcome translation
        self.translate_and_load("வணக்கம் எனக்கு உதவி வேண்டும்")

    def _build_header(self):
        header = tk.Frame(self, bg="#262a36", height=65)
        header.pack(fill=tk.X, side=tk.TOP)

        title = tk.Label(
            header,
            text="🤟 TEXT & VOICE TO SIGN LANGUAGE TRANSLATOR",
            font=("Segoe UI", 15, "bold"),
            fg="#00e5ff",
            bg="#262a36"
        )
        title.pack(side=tk.LEFT, padx=20, pady=12)

        subtitle = tk.Label(
            header,
            text="Bridging Hearing & Deaf Communication with Interactive Visual Signs (தமிழ் & English)",
            font=("Segoe UI", 10, "italic"),
            fg="#9aa0b4",
            bg="#262a36"
        )
        subtitle.pack(side=tk.LEFT, padx=5, pady=16)

    def _build_input_panel(self):
        input_frame = tk.LabelFrame(
            self,
            text=" 1. Enter Text (English or தமிழ்) or Speak via Microphone ",
            font=("Segoe UI", 11, "bold"),
            fg="#9aa0b4",
            bg="#20232c",
            bd=1,
            relief=tk.SOLID
        )
        input_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        entry_row = tk.Frame(input_frame, bg="#20232c")
        entry_row.pack(fill=tk.X, padx=15, pady=12)

        self.text_entry = tk.Entry(
            entry_row,
            font=("Segoe UI", 13),
            bg="#13151b",
            fg="#ffffff",
            insertbackground="white",
            bd=1,
            relief=tk.SOLID
        )
        self.text_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.text_entry.insert(0, "வணக்கம் எனக்கு உதவி வேண்டும்")
        self.text_entry.bind("<Return>", lambda event: self.on_translate())

        self.btn_translate = tk.Button(
            entry_row,
            text="✨ Translate to Signs",
            font=("Segoe UI", 10, "bold"),
            bg="#00b4d8",
            fg="#ffffff",
            activebackground="#0096c7",
            bd=0,
            padx=15,
            pady=6,
            cursor="hand2",
            command=self.on_translate
        )
        self.btn_translate.pack(side=tk.LEFT, padx=4)

        self.btn_mic_ta = tk.Button(
            entry_row,
            text="🎙️ தமிழ் Mic",
            font=("Segoe UI", 10, "bold"),
            bg="#7209b7",
            fg="#ffffff",
            activebackground="#560bad",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_mic_input(lang='ta-IN')
        )
        self.btn_mic_ta.pack(side=tk.LEFT, padx=4)

        self.btn_mic_en = tk.Button(
            entry_row,
            text="🎙️ English Mic",
            font=("Segoe UI", 10, "bold"),
            bg="#4361ee",
            fg="#ffffff",
            activebackground="#3a0ca3",
            bd=0,
            padx=12,
            pady=6,
            cursor="hand2",
            command=lambda: self.on_mic_input(lang='en-US')
        )
        self.btn_mic_en.pack(side=tk.LEFT, padx=4)

    def _build_player_panel(self):
        player_frame = tk.Frame(self, bg="#1a1c23")
        player_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=5)

        # Left Display Card: Visual Hand Diagram Canvas
        self.canvas_card = tk.LabelFrame(
            player_frame,
            text=" 2. Animated Sign Language Display ",
            font=("Segoe UI", 11, "bold"),
            fg="#9aa0b4",
            bg="#20232c",
            bd=1,
            relief=tk.SOLID
        )
        self.canvas_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.img_label = tk.Label(self.canvas_card, bg="#0d0e12")
        self.img_label.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # Info & Controls row
        info_row = tk.Frame(self.canvas_card, bg="#20232c")
        info_row.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.sign_title_label = tk.Label(
            info_row,
            text="SIGN: READY",
            font=("Segoe UI", 16, "bold"),
            fg="#00e5ff",
            bg="#20232c"
        )
        self.sign_title_label.pack(side=tk.LEFT)

        self.sign_tamil_label = tk.Label(
            info_row,
            text="தமிழ்: -",
            font=("Segoe UI", 13, "bold"),
            fg="#00e676",
            bg="#20232c"
        )
        self.sign_tamil_label.pack(side=tk.LEFT, padx=15)

        self.sign_desc_label = tk.Label(
            info_row,
            text="Description: Standby",
            font=("Segoe UI", 10, "italic"),
            fg="#8d99ae",
            bg="#20232c"
        )
        self.sign_desc_label.pack(side=tk.RIGHT)

        # Playback Controls Bar
        ctrl_bar = tk.Frame(self.canvas_card, bg="#1a1c23")
        ctrl_bar.pack(fill=tk.X, padx=15, pady=(0, 10))

        self.btn_prev = tk.Button(
            ctrl_bar, text="⏮ Prev", font=("Segoe UI", 9, "bold"),
            bg="#2b3040", fg="#ffffff", bd=0, padx=12, pady=5,
            cursor="hand2", command=self.on_prev
        )
        self.btn_prev.pack(side=tk.LEFT, padx=4)

        self.btn_play = tk.Button(
            ctrl_bar, text="▶ Play", font=("Segoe UI", 9, "bold"),
            bg="#00b4d8", fg="#ffffff", bd=0, padx=18, pady=5,
            cursor="hand2", command=self.on_play_toggle
        )
        self.btn_play.pack(side=tk.LEFT, padx=4)

        self.btn_next = tk.Button(
            ctrl_bar, text="⏭ Next", font=("Segoe UI", 9, "bold"),
            bg="#2b3040", fg="#ffffff", bd=0, padx=12, pady=5,
            cursor="hand2", command=self.on_next
        )
        self.btn_next.pack(side=tk.LEFT, padx=4)

        # Speed slider
        lbl_speed = tk.Label(ctrl_bar, text="Speed:", font=("Segoe UI", 9), fg="#adb5bd", bg="#1a1c23")
        lbl_speed.pack(side=tk.LEFT, padx=(20, 5))

        self.speed_slider = tk.Scale(
            ctrl_bar, from_=0.3, to=2.0, resolution=0.1, orient=tk.HORIZONTAL,
            bg="#1a1c23", fg="#ffffff", highlightthickness=0, length=120,
            command=self.on_speed_change
        )
        self.speed_slider.set(self.playback_speed)
        self.speed_slider.pack(side=tk.LEFT, padx=5)

        # Language option for audio
        lbl_voice = tk.Label(ctrl_bar, text="Voice:", font=("Segoe UI", 9), fg="#adb5bd", bg="#1a1c23")
        lbl_voice.pack(side=tk.LEFT, padx=(15, 4))

        rb_ta = tk.Radiobutton(ctrl_bar, text="தமிழ்", variable=self.audio_lang_var, value="ta",
                               bg="#1a1c23", fg="#00e676", selectcolor="#20232c", font=("Segoe UI", 9, "bold"))
        rb_ta.pack(side=tk.LEFT)

        rb_en = tk.Radiobutton(ctrl_bar, text="English", variable=self.audio_lang_var, value="en",
                               bg="#1a1c23", fg="#00e5ff", selectcolor="#20232c", font=("Segoe UI", 9))
        rb_en.pack(side=tk.LEFT, padx=4)

        chk_speech = tk.Checkbutton(
            ctrl_bar, text="Speak Audio", variable=self.speak_while_signing,
            bg="#1a1c23", fg="#e0e0e0", selectcolor="#20232c", font=("Segoe UI", 9)
        )
        chk_speech.pack(side=tk.RIGHT, padx=10)

    def _build_timeline_panel(self):
        timeline_frame = tk.LabelFrame(
            self,
            text=" 3. Sign Gesture Sequence Timeline ",
            font=("Segoe UI", 11, "bold"),
            fg="#9aa0b4",
            bg="#20232c",
            bd=1,
            relief=tk.SOLID
        )
        timeline_frame.pack(fill=tk.X, padx=20, pady=(5, 15))

        self.timeline_listbox = tk.Listbox(
            timeline_frame,
            height=4,
            font=("Segoe UI", 10),
            bg="#13151b",
            fg="#ffffff",
            selectbackground="#00b4d8",
            selectforeground="#ffffff",
            bd=0
        )
        self.timeline_listbox.pack(fill=tk.X, padx=15, pady=10)
        self.timeline_listbox.bind("<<ListboxSelect>>", self.on_timeline_select)

    def on_translate(self):
        text = self.text_entry.get().strip()
        if not text:
            return
        self.translate_and_load(text)

    def on_mic_input(self, lang: str = 'ta-IN'):
        self.sign_desc_label.config(text=f"[STT] Listening for microphone input ({lang})...")
        self.update()

        def _worker():
            transcript = self.engine.speech_to_text(language=lang)
            if not transcript.startswith("["):
                self.text_entry.delete(0, tk.END)
                self.text_entry.insert(0, transcript)
                self.translate_and_load(transcript)
            else:
                self.sign_desc_label.config(text=transcript)

        threading.Thread(target=_worker, daemon=True).start()

    def translate_and_load(self, text: str):
        self.tokens = self.engine.translate_text(text)
        self.current_index = 0
        self.is_playing = False
        self.btn_play.config(text="▶ Play", bg="#00b4d8")

        self.timeline_listbox.delete(0, tk.END)
        for idx, t in enumerate(self.tokens):
            tok_name = t['token']
            typ = t['type'].upper()
            tam = t.get('tamil', '')
            trans = t.get('transliteration', '')
            self.timeline_listbox.insert(tk.END, f" Step {idx+1}: [{typ}] {tok_name} ➔ {tam} ({trans})")

        if self.tokens:
            self.display_sign(self.current_index)

    def display_sign(self, index: int):
        if not self.tokens or index >= len(self.tokens):
            return

        item = self.tokens[index]
        sign_token = item['token']
        tamil_t = item.get('tamil', '')
        translit_t = item.get('transliteration', '')
        desc = item.get('description', '')

        self.sign_title_label.config(text=f"SIGN: {sign_token}")
        self.sign_tamil_label.config(text=f"தமிழ்: {tamil_t} ({translit_t})")
        self.sign_desc_label.config(text=f"Description: {desc}")

        self.timeline_listbox.selection_clear(0, tk.END)
        self.timeline_listbox.selection_set(index)
        self.timeline_listbox.see(index)

        # Generate & render diagram
        img_bgr = self.engine.render_sign_image(sign_token, width=640, height=440)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        self.img_label.imgtk = img_tk
        self.img_label.configure(image=img_tk)

        # Speech output
        if self.speak_while_signing.get() and sign_token != "SPACE":
            if self.audio_lang_var.get() == "ta":
                self.tts.speak(tamil_t, lang='ta')
            else:
                self.tts.speak(sign_token, lang='en')

    def on_play_toggle(self):
        if self.is_playing:
            self.is_playing = False
            self.btn_play.config(text="▶ Play", bg="#00b4d8")
        else:
            self.is_playing = True
            self.btn_play.config(text="⏸ Pause", bg="#d90429")
            self._playback_loop()

    def _playback_loop(self):
        if not self.is_playing or not self.tokens:
            return

        self.display_sign(self.current_index)

        if self.current_index < len(self.tokens) - 1:
            self.current_index += 1
            delay_ms = int(self.playback_speed * 1000)
            self.after(delay_ms, self._playback_loop)
        else:
            self.is_playing = False
            self.btn_play.config(text="▶ Replay", bg="#00b4d8")

    def on_next(self):
        if self.tokens:
            self.current_index = (self.current_index + 1) % len(self.tokens)
            self.display_sign(self.current_index)

    def on_prev(self):
        if self.tokens:
            self.current_index = (self.current_index - 1) % len(self.tokens)
            self.display_sign(self.current_index)

    def on_speed_change(self, val):
        self.playback_speed = float(val)

    def on_timeline_select(self, event):
        sel = self.timeline_listbox.curselection()
        if sel:
            self.current_index = sel[0]
            self.display_sign(self.current_index)


if __name__ == "__main__":
    app = TextToSignApp()
    app.mainloop()
