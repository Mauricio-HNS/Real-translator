from __future__ import annotations

from typing import Protocol

import speech_recognition as sr


class STTProvider(Protocol):
    def transcribe(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> str:
        ...


class GoogleSTTProvider:
    def __init__(self, language: str = "en-US") -> None:
        self._language = language

    def transcribe(self, recognizer: sr.Recognizer, audio: sr.AudioData) -> str:
        return recognizer.recognize_google(audio, language=self._language).strip()
