from __future__ import annotations

from real_time_translator.translation.provider import TranslationProvider


class Translator:
    def __init__(self, provider: TranslationProvider) -> None:
        self._provider = provider

    def translate(self, text: str) -> str:
        return self._provider.translate(text)
