from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl, field_validator
from typing import List


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ────────────────────────────────────────────────────────────
    APP_NAME: str = "samarth-backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    # ── Supabase ───────────────────────────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ── Gemini (Stage 7+) ──────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    # ── CORS ───────────────────────────────────────────────────────────────────
    # e.g. FRONTEND_URL=http://localhost:5173
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("FRONTEND_URL", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str) -> str:
        return v.strip().rstrip("/")

    @property
    def cors_origins(self) -> List[str]:
        """Return all allowed CORS origins."""
        origins = [self.FRONTEND_URL]
        # Always allow localhost variants for development
        origins += [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
        ]
        return list(set(origins))


settings = Settings()
