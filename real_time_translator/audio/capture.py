from __future__ import annotations

import audioop
import threading
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
        self._stop_listening = None

    @property
    def recognizer(self) -> sr.Recognizer:
        return self._recognizer

    def calibrate(self) -> None:
        with self._op_lock:
            with sr.Microphone(device_index=self._device_index) as source:
                self._recognizer.adjust_for_ambient_noise(
                    source,
                    duration=self._config.ambient_adjust_seconds,
                )

    def smart_calibrate(self, passes: int = 3, seconds: float = 0.5) -> None:
        total_passes = max(1, min(6, int(passes)))
        duration = max(0.3, min(2.0, float(seconds)))
        for _ in range(total_passes):
            self.recalibrate(seconds=duration)

    def probe_microphone_permission(self) -> None:
        # Opening the microphone stream triggers macOS permission prompt if needed.
        with self._op_lock:
            with sr.Microphone(device_index=self._device_index) as source:
                self._recognizer.record(source, duration=0.2)

    def recalibrate(self, seconds: float = 1.0) -> None:
        with self._op_lock:
            with sr.Microphone(device_index=self._device_index) as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=max(0.3, seconds))

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

    def start(self, callback: Callable[[sr.Recognizer, sr.AudioData], None]) -> None:
        with self._op_lock:
            if self._stop_listening is not None:
                self._stop_listening(wait_for_stop=False)
                self._stop_listening = None
            source = sr.Microphone(device_index=self._device_index)
            self._stop_listening = self._recognizer.listen_in_background(
                source,
                callback,
                phrase_time_limit=self._config.phrase_time_limit_seconds,
            )

    def capture_level(self, seconds: float = 0.8) -> int:
        duration = max(0.2, min(3.0, float(seconds)))
        with self._op_lock:
            with sr.Microphone(device_index=self._device_index) as source:
                audio = self._recognizer.record(source, duration=duration)
        raw = audio.get_raw_data(convert_rate=16000, convert_width=2)
        return int(audioop.rms(raw, 2))

    def listen_once(self, seconds: float = 2.5) -> sr.AudioData:
        duration = max(0.8, min(6.0, float(seconds)))
        with self._op_lock:
            with sr.Microphone(device_index=self._device_index) as source:
                return self._recognizer.record(source, duration=duration)

    def stop(self) -> None:
        with self._op_lock:
            if self._stop_listening is not None:
                self._stop_listening(wait_for_stop=False)
                self._stop_listening = None

    @staticmethod
    def list_microphones() -> list[str]:
        return list(sr.Microphone.list_microphone_names())
