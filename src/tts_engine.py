"""
Bilingual Text-to-Speech (TTS) Engine Module
Supports high-performance English and Tamil speech synthesis:
- English: Offline, zero-latency synthesis via pyttsx3 (or studio gTTS).
- Tamil: Studio-quality natural neural Tamil speech via gTTS + local audio caching.
- Auto-Language Detection: Automatically detects Tamil script and routes speech.
- Asynchronous & Non-Blocking: Dedicated background thread ensures the camera stream never lags.
"""

import os
import queue
import re
import tempfile
import threading
import time
from typing import Optional, Dict

import pyttsx3
try:
    import pythoncom
except ImportError:
    pythoncom = None

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

try:
    from gtts import gTTS
    _GTTS_AVAILABLE = True
except ImportError:
    _GTTS_AVAILABLE = False


class TTSEngine:
    """Thread-safe, non-blocking bilingual Text-to-Speech Engine."""

    def __init__(self, rate: int = 160, volume: float = 1.0, voice_index: int = 0, default_lang: str = "en"):
        self._queue = queue.Queue()
        self._running = True
        self._is_speaking = False
        self._rate = rate
        self._volume = volume
        self._voice_index = voice_index
        self._default_lang = default_lang
        self._last_spoken_text = ""
        self._last_spoken_lang = "en"

        # Initialize audio cache directory for ultra-fast instant playback of common phrases
        self._cache_dir = os.path.join(os.path.dirname(__file__), "..", "assets", "audio_cache")
        os.makedirs(self._cache_dir, exist_ok=True)

        # Initialize pygame audio mixer for MP3 playback if available
        self._pygame_initialized = False
        if _PYGAME_AVAILABLE:
            try:
                pygame.mixer.init()
                self._pygame_initialized = True
            except Exception as e:
                print(f"[TTS] Warning: Could not initialize pygame mixer: {e}")

        # Fetch available system voices upfront
        self.available_voices = []
        try:
            temp_engine = pyttsx3.init()
            voices = temp_engine.getProperty('voices')
            self.available_voices = [{'id': v.id, 'name': v.name} for v in voices]
            del temp_engine
        except Exception as e:
            print(f"[TTS] Warning: Failed to query system voices: {e}")

        # Start dedicated background worker thread
        self._worker_thread = threading.Thread(target=self._run_worker, daemon=True)
        self._worker_thread.start()

    @staticmethod
    def is_tamil(text: str) -> bool:
        """Checks if text contains Tamil Unicode characters."""
        return bool(re.search(r'[\u0b80-\u0bff]', text))

    def _get_cache_filename(self, text: str, lang: str) -> str:
        """Generates a clean filesystem-safe cache path."""
        safe_name = re.sub(r'[^\w\-_]', '_', text.strip())[:30]
        return os.path.join(self._cache_dir, f"{lang}_{safe_name}.mp3")

    def _play_audio_file(self, file_path: str):
        """Plays an audio file through pygame mixer synchronously inside worker."""
        if not self._pygame_initialized:
            return

        try:
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.set_volume(self._volume)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy() and self._running:
                time.sleep(0.05)
        except Exception as e:
            print(f"[TTS] Audio playback error ({file_path}): {e}")

    def _speak_tamil(self, text: str):
        """Generates and plays Tamil audio using gTTS and local caching."""
        cache_file = self._get_cache_filename(text, "ta")

        # Use cached audio file if already generated
        if os.path.exists(cache_file) and os.path.getsize(cache_file) > 100:
            self._play_audio_file(cache_file)
            return

        if not _GTTS_AVAILABLE:
            print(f"[TTS] Tamil audio requested for '{text}', but gTTS is not installed.")
            return

        try:
            tts = gTTS(text=text, lang='ta', slow=False)
            tts.save(cache_file)
            self._play_audio_file(cache_file)
        except Exception as e:
            print(f"[TTS] Tamil gTTS generation error for '{text}': {e}")
            # If network error, try temp file or notify
            try:
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tf:
                    temp_path = tf.name
                tts = gTTS(text=text, lang='ta', slow=False)
                tts.save(temp_path)
                self._play_audio_file(temp_path)
                os.remove(temp_path)
            except Exception:
                pass

    def _run_worker(self):
        """Worker thread loop consuming speech tasks from queue."""
        if pythoncom:
            pythoncom.CoInitialize()

        engine = None
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', self._rate)
            engine.setProperty('volume', self._volume)
            voices = engine.getProperty('voices')
            if voices and 0 <= self._voice_index < len(voices):
                engine.setProperty('voice', voices[self._voice_index].id)
        except Exception as e:
            print(f"[TTS] pyttsx3 initialization note: {e}")

        while self._running:
            try:
                task = self._queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if task is None:
                break

            action, data = task

            if action == 'SPEAK':
                text, lang = data
                self._is_speaking = True

                # Determine effective language: explicit or auto-detected
                effective_lang = lang or self._default_lang
                if self.is_tamil(text):
                    effective_lang = 'ta'

                try:
                    if effective_lang == 'ta':
                        self._speak_tamil(text)
                    else:
                        # English speech synthesis via pyttsx3
                        if engine is not None:
                            engine.say(text)
                            engine.runAndWait()
                        elif _GTTS_AVAILABLE and self._pygame_initialized:
                            # Fallback to gTTS English if pyttsx3 is unavailable
                            cache_file = self._get_cache_filename(text, "en")
                            if not os.path.exists(cache_file):
                                gtts_en = gTTS(text=text, lang='en')
                                gtts_en.save(cache_file)
                            self._play_audio_file(cache_file)
                except Exception as err:
                    print(f"[TTS] Error during speech synthesis: {err}")
                finally:
                    self._is_speaking = False
                    self._last_spoken_text = text
                    self._last_spoken_lang = effective_lang

            elif action == 'SET_RATE' and engine is not None:
                self._rate = data
                try:
                    engine.setProperty('rate', self._rate)
                except Exception:
                    pass

            elif action == 'SET_VOLUME':
                self._volume = data
                if engine is not None:
                    try:
                        engine.setProperty('volume', self._volume)
                    except Exception:
                        pass
                if self._pygame_initialized:
                    try:
                        pygame.mixer.music.set_volume(self._volume)
                    except Exception:
                        pass

            elif action == 'SET_VOICE' and engine is not None:
                self._voice_index = data
                voices = engine.getProperty('voices')
                if voices and 0 <= self._voice_index < len(voices):
                    try:
                        engine.setProperty('voice', voices[self._voice_index].id)
                    except Exception:
                        pass

            elif action == 'SET_DEFAULT_LANG':
                self._default_lang = data

            self._queue.task_done()

        if pythoncom:
            pythoncom.CoUninitialize()

    def speak(self, text: str, lang: Optional[str] = None) -> bool:
        """
        Enqueue text to be spoken.
        Args:
            text: Sentence or word to synthesize.
            lang: 'en' for English, 'ta' for Tamil, or None for auto-detection / default.
        """
        cleaned = text.strip()
        if not cleaned:
            return False

        self._queue.put(('SPEAK', (cleaned, lang)))
        return True

    def set_default_language(self, lang: str):
        """Set default language ('en' or 'ta')."""
        self._default_lang = lang
        self._queue.put(('SET_DEFAULT_LANG', lang))

    def set_rate(self, rate: int):
        """Adjust speech rate (speed). Typical range: 100 - 250 wpm."""
        self._queue.put(('SET_RATE', rate))

    def set_volume(self, volume: float):
        """Adjust volume (0.0 to 1.0)."""
        self._queue.put(('SET_VOLUME', max(0.0, min(1.0, volume))))

    def set_voice(self, voice_index: int):
        """Select voice by index."""
        self._queue.put(('SET_VOICE', voice_index))

    @property
    def is_speaking(self) -> bool:
        """Returns True if the engine is actively speaking audio."""
        return self._is_speaking

    @property
    def last_spoken(self) -> str:
        return self._last_spoken_text

    @property
    def last_lang(self) -> str:
        return self._last_spoken_lang

    def stop(self):
        """Gracefully stop TTS worker."""
        self._running = False
        self._queue.put(None)
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)
