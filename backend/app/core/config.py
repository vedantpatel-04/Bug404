"""
ShelfIQ Backend — Central Configuration.

Reads all settings from environment variables via Pydantic Settings.
Defaults are provided for local development.
"""
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


# Project root (Bug404/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────────────
    ENVIRONMENT: str = Field(default="development", description="development | staging | production")
    APP_NAME: str = "ShelfIQ"
    APP_VERSION: str = "3.0.0"
    DEBUG: bool = True
    TIMEZONE: str = "Asia/Kolkata"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:8501"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default=f"sqlite+aiosqlite:///{PROJECT_ROOT / 'database' / 'retail_shelf.db'}",
        description="Async database URL. Use postgresql+asyncpg:// for production.",
    )

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    # ── JWT Authentication ───────────────────────────────────
    JWT_SECRET_KEY: str = Field(
        default="shelfiq-dev-secret-change-in-production-please",
        description="HMAC secret for dev. In production use RS256 with key files.",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── WhatsApp Business API ────────────────────────────────
    WHATSAPP_ACCESS_TOKEN: str = ""
    WHATSAPP_PHONE_NUMBER_ID: str = ""
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: str = "shelfiq-webhook-verify-dev"
    WHATSAPP_WEBHOOK_SECRET: str = ""
    WHATSAPP_API_VERSION: str = "v18.0"

    # ── Razorpay ─────────────────────────────────────────────
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""

    # ── Encryption ───────────────────────────────────────────
    FIELD_ENCRYPTION_KEY: str = Field(
        default="0123456789abcdef0123456789abcdef",  # 32-byte hex for dev only
        description="AES-256 key for encrypting phone numbers and RTSP URLs.",
    )

    # ── Sentry ───────────────────────────────────────────────
    SENTRY_DSN: str = ""

    # ── Paths (derived from project root) ────────────────────
    @property
    def project_root(self) -> Path:
        return PROJECT_ROOT

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.DATABASE_URL

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


# Singleton
settings = Settings()
