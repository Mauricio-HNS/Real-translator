from __future__ import annotations

from typing import Protocol

from deep_translator import GoogleTranslator


class TranslationProvider(Protocol):
    def translate(self, text: str) -> str:
        ...


class GoogleTranslationProvider:
    def __init__(self, source: str = "en", target: str = "pt") -> None:
        self._translator = GoogleTranslator(source=source, target=target)

    def translate(self, text: str) -> str:
        if not text.strip():
            return ""
        return self._translator.translate(text).strip()
