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
        detailed = recognizer.recognize_google(audio, language=self._language, show_all=True)
        if isinstance(detailed, dict):
            alternatives = detailed.get("alternative", []) or []
            if alternatives:
                # Prefer high confidence; fallback to longer transcript when confidence is missing.
                best = max(
                    alternatives,
                    key=lambda alt: (
                        float(alt.get("confidence", 0.0)),
                        len(str(alt.get("transcript", ""))),
                    ),
                )
                text = str(best.get("transcript", "")).strip()
                if text:
                    return text
        return recognizer.recognize_google(audio, language=self._language).strip()
