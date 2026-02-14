from __future__ import annotations

import audioop
import threading
import time
from typing import Callable, Optional

import speech_recognition as sr

from real_time_translator.config import AppConfig


class AudioCapture:
    def __init__(self, config: AppConfig, device_index: Optional[int] = None) -> None:
        self._config = config
        self._device_index = device_index
        self._recognizer = sr.Recognizer()
        self._recognizer.energy_threshold = config.energy_threshold
        self._recognizer.dynamic_energy_threshold = True
        self._recognizer.pause_threshold = 0.6
        self._op_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._worker_stop = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None
        self._capture_active = threading.Event()

    @property
    def recognizer(self) -> sr.Recognizer:
        return self._recognizer

    def calibrate(self) -> None:
        self._with_microphone_retry(
            lambda source: self._recognizer.adjust_for_ambient_noise(
                source,
                duration=self._config.ambient_adjust_seconds,
            )
        )

    def smart_calibrate(self, passes: int = 3, seconds: float = 0.5) -> None:
        total_passes = max(1, min(6, int(passes)))
        duration = max(0.3, min(2.0, float(seconds)))
        for _ in range(total_passes):
            self.recalibrate(seconds=duration)

    def probe_microphone_permission(self) -> None:
        # Opening the microphone stream triggers macOS permission prompt if needed.
        self._with_microphone_retry(lambda source: self._recognizer.record(source, duration=0.2))

    def recalibrate(self, seconds: float = 1.0) -> None:
        self._with_microphone_retry(
            lambda source: self._recognizer.adjust_for_ambient_noise(source, duration=max(0.3, seconds))
        )

    def set_sensitivity(
        self,
        mode: str,
        manual_threshold: int,
        pause_threshold: float = 0.6,
    ) -> None:
        normalized_mode = (mode or "auto").strip().lower()
        self._recognizer.pause_threshold = max(0.2, min(1.5, pause_threshold))
        if normalized_mode == "manual":
            self._recognizer.dynamic_energy_threshold = False
            self._recognizer.energy_threshold = max(100, min(4000, int(manual_threshold)))
        else:
            self._recognizer.dynamic_energy_threshold = True
            # Auto mode tuned for distant speech (~1m): keep a lower floor and react faster.
            self._recognizer.energy_threshold = max(70, min(1200, int(manual_threshold)))
            self._recognizer.dynamic_energy_adjustment_damping = 0.1
            self._recognizer.dynamic_energy_ratio = 1.2

    def start(self, callback: Callable[[sr.Recognizer, sr.AudioData], None]) -> None:
        self.stop()
        with self._state_lock:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                raise RuntimeError("Previous audio worker is still shutting down. Try again in a moment.")
            with self._op_lock:
                self._worker_stop.clear()

        def loop() -> None:
            try:
                with self._op_lock:
                    self._capture_active.set()
                    microphone = self._create_microphone_with_retry()
                    with microphone as source:
                        while not self._worker_stop.is_set():
                            audio = self._recognizer.record(
                                source,
                                duration=max(0.8, float(self._config.phrase_time_limit_seconds)),
                            )
                            callback(self._recognizer, audio)
            except Exception:
                # Let controller surface status/errors; avoid crashing whole process.
                return
            finally:
                self._capture_active.clear()

        self._worker_thread = threading.Thread(target=loop, daemon=True, name="audio-capture-loop")
        self._worker_thread.start()

    def capture_level(self, seconds: float = 0.8) -> int:
        duration = max(0.2, min(3.0, float(seconds)))
        audio = self._with_microphone_retry(lambda source: self._recognizer.record(source, duration=duration))
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        return int(audioop.rms(raw, 2))

    def listen_once(self, seconds: float = 2.5) -> sr.AudioData:
        duration = max(0.8, min(6.0, float(seconds)))
        return self._with_microphone_retry(lambda source: self._recognizer.record(source, duration=duration))

    def stop(self) -> None:
        with self._state_lock:
            self._worker_stop.set()
            thread = self._worker_thread
            if thread is not None and thread.is_alive():
                timeout = max(2.0, float(self._config.phrase_time_limit_seconds) + 1.0)
                thread.join(timeout=timeout)
                if thread.is_alive():
                    return
            self._worker_thread = None
            self._capture_active.clear()

    def _create_microphone_with_retry(self, retries: int = 2) -> sr.Microphone:
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                return sr.Microphone(device_index=self._device_index)
            except AssertionError as exc:
                last_exc = exc
                if attempt >= retries:
                    raise
                time.sleep(0.12)
        raise RuntimeError(f"Microphone open failed: {last_exc!r}")

    def _with_microphone_retry(self, fn: Callable[[sr.Microphone], object], retries: int = 2):
        with self._op_lock:
            if self._capture_active.is_set():
                raise RuntimeError("Cannot run this action while listening. Stop first.")
            last_exc: Exception | None = None
            for attempt in range(retries + 1):
                try:
                    microphone = self._create_microphone_with_retry(retries=1)
                    with microphone as source:
                        return fn(source)
                except AssertionError as exc:
                    last_exc = exc
                    if attempt >= retries:
                        raise
                    time.sleep(0.15)
            raise RuntimeError(f"Microphone action failed: {last_exc!r}")

    @staticmethod
    def list_microphones() -> list[str]:
        return list(sr.Microphone.list_microphone_names())
