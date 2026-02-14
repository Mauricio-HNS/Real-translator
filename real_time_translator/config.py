from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    source_speech_language: str = "en-US"
    source_translation_language: str = "en"
    target_translation_language: str = "pt"
    phrase_time_limit_seconds: int = 3
    ambient_adjust_seconds: float = 1.0
    energy_threshold: int = 300


DEFAULT_CONFIG = AppConfig()
