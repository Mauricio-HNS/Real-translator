from __future__ import annotations

import queue
import threading
from datetime import datetime

import speech_recognition as sr

from real_time_translator.audio.capture import AudioCapture
from real_time_translator.config import DEFAULT_CONFIG
from real_time_translator.stt.provider import GoogleSTTProvider
from real_time_translator.translation.provider import GoogleTranslationProvider
from real_time_translator.translation.translator import Translator
from real_time_translator.ui.window import MainWindow


class AppController:
    def __init__(self) -> None:
        self._capture = AudioCapture(DEFAULT_CONFIG)
        self._stt = GoogleSTTProvider(language=DEFAULT_CONFIG.source_speech_language)
        self._translator = Translator(
            GoogleTranslationProvider(
                source=DEFAULT_CONFIG.source_translation_language,
                target=DEFAULT_CONFIG.target_translation_language,
            )
        )
        self._messages: "queue.Queue[tuple[str, str]]" = queue.Queue()
        self._running = False
        self._lock = threading.Lock()

        self._window = MainWindow(on_start=self.start, on_stop=self.stop)
        self._window.root.after(100, self._drain_messages)

    def _audio_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        if not self._running:
            return
        try:
            original = self._stt.transcribe(recognizer, audio)
            if not original:
                return
            translated = self._translator.translate(original)
            stamp = datetime.now().strftime("%H:%M:%S")
            self._messages.put((f"[{stamp}] {original}", f"[{stamp}] {translated}"))
        except sr.UnknownValueError:
            return
        except sr.RequestError as exc:
            self._messages.put(("", f"[STT error] {exc}"))
        except Exception as exc:
            self._messages.put(("", f"[Translate error] {exc}"))

    def _drain_messages(self) -> None:
        try:
            while True:
                original, translated = self._messages.get_nowait()
                if original:
                    self._window.append(original, translated)
                else:
                    self._window.set_status(translated)
        except queue.Empty:
            pass
        finally:
            self._window.root.after(100, self._drain_messages)

    def start(self) -> None:
        with self._lock:
            if self._running:
                return
            self._window.set_status("Calibrating microphone...")
            self._capture.calibrate()
            self._capture.start(self._audio_callback)
            self._running = True
            self._window.set_status("Listening...")

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            self._capture.stop()
            self._running = False
            self._window.set_status("Stopped")

    def run(self) -> None:
        self._window.run()


if __name__ == "__main__":
    AppController().run()
