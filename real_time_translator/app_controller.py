from __future__ import annotations

import threading
from datetime import datetime

import speech_recognition as sr

from real_time_translator.audio.capture import AudioCapture
from real_time_translator.config import DEFAULT_CONFIG
from real_time_translator.stt.provider import GoogleSTTProvider
from real_time_translator.translation.provider import GoogleTranslationProvider
from real_time_translator.translation.translator import Translator


class AppController:
    def __init__(self, mic_index: int | None = None) -> None:
        self._mic_index = mic_index
        self._capture = AudioCapture(DEFAULT_CONFIG, device_index=self._mic_index)
        self._stt = GoogleSTTProvider(language=DEFAULT_CONFIG.source_speech_language)
        self._translator = Translator(
            GoogleTranslationProvider(
                source=DEFAULT_CONFIG.source_translation_language,
                target=DEFAULT_CONFIG.target_translation_language,
            )
        )
        self._running = False
        self._status = "Ready"
        self._sensitivity_mode = "auto"
        self._manual_threshold = DEFAULT_CONFIG.energy_threshold
        self._pause_threshold = 0.6
        self._original_lines: list[str] = []
        self._translated_lines: list[str] = []
        self._lock = threading.Lock()
        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

    @staticmethod
    def list_microphones() -> list[str]:
        return AudioCapture.list_microphones()

    @property
    def mic_index(self) -> int | None:
        return self._mic_index

    def set_microphone(self, mic_index: int | None) -> str:
        with self._lock:
            if self._running:
                return "Stop listening before changing microphone."
            self._mic_index = mic_index
            self._capture = AudioCapture(DEFAULT_CONFIG, device_index=self._mic_index)
            self._capture.set_sensitivity(
                mode=self._sensitivity_mode,
                manual_threshold=self._manual_threshold,
                pause_threshold=self._pause_threshold,
            )
            self._status = f"Microphone set to index: {self._mic_index if self._mic_index is not None else 'default'}"
            return self._status

    def auto_select_microphone(self) -> str:
        names = self.list_microphones()
        if not names:
            with self._lock:
                self._status = "No microphone detected."
                return self._status

        for index in range(len(names)):
            try:
                probe = AudioCapture(DEFAULT_CONFIG, device_index=index)
                probe.probe_microphone_permission()
                return self.set_microphone(index)
            except Exception:  # noqa: BLE001
                continue

        with self._lock:
            self._status = "Could not open any microphone input."
            return self._status

    def test_microphone_level(self, seconds: float = 1.0) -> str:
        try:
            level = self._capture.capture_level(seconds=seconds)
            with self._lock:
                self._status = f"Mic level={level} (good speech usually > 250)"
                return self._status
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Mic test failed: {exc}"
                return self._status

    def request_microphone_access(self) -> str:
        try:
            self._capture.probe_microphone_permission()
            with self._lock:
                self._status = "Microphone access ok"
                return self._status
        except sr.WaitTimeoutError:
            with self._lock:
                self._status = "Microphone access ok (silence)"
                return self._status
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Microphone permission error: {exc}"
                return self._status

    def _audio_callback(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> None:
        if not self._running:
            return

        try:
            original = self._stt.transcribe(recognizer, audio)
            if not original:
                return
            translated = self._translator.translate(original)
            stamp = datetime.now().strftime("%H:%M:%S")

            with self._lock:
                self._original_lines.append(f"[{stamp}] {original}")
                self._translated_lines.append(f"[{stamp}] {translated}")
                self._original_lines = self._original_lines[-300:]
                self._translated_lines = self._translated_lines[-300:]
        except sr.UnknownValueError:
            return
        except sr.RequestError as exc:
            with self._lock:
                self._status = f"STT error: {exc}"
        except Exception as exc:  # noqa: BLE001
            with self._lock:
                self._status = f"Translation error: {exc}"

    def start(self) -> str:
        with self._lock:
            if self._running:
                return self._status
            self._status = "Calibrating microphone..."

        if self._sensitivity_mode == "auto":
            self._capture.smart_calibrate(passes=3, seconds=0.5)
        else:
            self._capture.calibrate()
        self._capture.start(self._audio_callback)

        with self._lock:
            self._running = True
            self._status = "Listening..."
            return self._status

    def apply_sensitivity(self, mode: str, manual_threshold: int, pause_threshold: float) -> str:
        with self._lock:
            self._sensitivity_mode = "manual" if (mode or "").lower() == "manual" else "auto"
            self._manual_threshold = int(manual_threshold)
            self._pause_threshold = float(pause_threshold)

        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

        with self._lock:
            effective = (
                f"manual={self._manual_threshold}"
                if self._sensitivity_mode == "manual"
                else "auto"
            )
            self._status = f"Sensitivity applied ({effective}, pause={self._pause_threshold:.2f})"
            return self._status

    def recalibrate(self, seconds: float = 1.0) -> str:
        with self._lock:
            was_running = self._running
            if was_running:
                self._running = False
        if was_running:
            self._capture.stop()

        self._capture.recalibrate(seconds=seconds)
        self._capture.set_sensitivity(
            mode=self._sensitivity_mode,
            manual_threshold=self._manual_threshold,
            pause_threshold=self._pause_threshold,
        )

        if was_running:
            self._capture.start(self._audio_callback)
            with self._lock:
                self._running = True

        with self._lock:
            self._status = f"Environment recalibrated ({seconds:.1f}s)"
            return self._status

    def stop(self) -> str:
        with self._lock:
            if not self._running:
                return self._status
            self._running = False

        self._capture.stop()

        with self._lock:
            self._status = "Stopped"
            return self._status

    def clear(self) -> str:
        with self._lock:
            self._original_lines.clear()
            self._translated_lines.clear()
            return self._status

    def snapshot(self) -> tuple[str, str, str]:
        with self._lock:
            return (
                self._status,
                "\n".join(self._original_lines),
                "\n".join(self._translated_lines),
            )

    def settings_snapshot(self) -> tuple[str, int, float]:
        with self._lock:
            return self._sensitivity_mode, self._manual_threshold, self._pause_threshold
