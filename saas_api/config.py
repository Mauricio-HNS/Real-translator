from __future__ import annotations

import os


class Settings:
    app_name: str = "Real Translator API"
    app_env: str = os.getenv("RT_API_ENV", "dev")
    db_url: str = os.getenv("RT_API_DB_URL", "sqlite:///./saas_api.db")
    stripe_secret_key: str = os.getenv("STRIPE_SECRET_KEY", "")
    stripe_webhook_secret: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    default_currency: str = os.getenv("RT_API_CURRENCY", "usd")
    whisper_model: str = os.getenv("RT_STT_MODEL", "small.en")
    enable_whisper: bool = os.getenv("RT_ENABLE_WHISPER", "1") == "1"


settings = Settings()

