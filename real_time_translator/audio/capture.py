from __future__ import annotations

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
        self._microphone = sr.Microphone(device_index=device_index)
        self._stop_listening = None

    @property
    def recognizer(self) -> sr.Recognizer:
        return self._recognizer

    def calibrate(self) -> None:
        with self._microphone as source:
            self._recognizer.adjust_for_ambient_noise(
                source,
                duration=self._config.ambient_adjust_seconds,
            )

    def recalibrate(self, seconds: float = 1.0) -> None:
        with self._microphone as source:
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
        with self._microphone as source:
            self._stop_listening = self._recognizer.listen_in_background(
                source,
                callback,
                phrase_time_limit=self._config.phrase_time_limit_seconds,
            )

    def stop(self) -> None:
        if self._stop_listening is not None:
            self._stop_listening(wait_for_stop=False)
            self._stop_listening = None

    @staticmethod
    def list_microphones() -> list[str]:
        return list(sr.Microphone.list_microphone_names())
