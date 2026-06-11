from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_ENV: str = "development"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    API_PREFIX: str = "/api/v1"

    DATABASE_URL: str = "postgresql+asyncpg://zuvra:zuvra@localhost:5432/zuvra"

    @property
    def async_database_url(self) -> str:
        """Normaliza la URL para asyncpg (Render provee postgresql://)."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    UNIGIS_WSDL_URL: str = ""
    UNIGIS_API_KEY: str = ""
    UNIGIS_LOGIN: str = ""
    UNIGIS_PASSWORD: str = ""

    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = "whatsapp:+14155238886"

    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "notificaciones@zuvra.io"
    SENDGRID_FROM_NAME: str = "Zuvra Compliance"

    SYNC_INTERVAL_MINUTES: int = 30
    NOTIFY_JOB_HOUR: int = 8
    NOTIFY_JOB_MINUTE: int = 0

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # API Key para autenticar el panel admin y llamadas internas
    # Generar con: python -c "import secrets; print(secrets.token_urlsafe(32))"
    ZUVRA_API_KEY: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
