from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    database_url: str = "postgresql+psycopg://atlas_booking:atlas_booking@localhost:5432/atlas_booking"
    app_url: str = "http://localhost:8000"
    timezone: str = "America/Mexico_City"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:8000"]
    slot_interval_minutes: int = 30
    seed_data: bool = True
    google_calendar_mode: Literal["disabled", "oauth"] = "disabled"
    google_calendar_id: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_refresh_token: str | None = None
    roberto_booking_url: str | None = None
    damian_booking_url: str | None = None

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        return value.split(",") if isinstance(value, str) else value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        """Railway exposes postgres URLs without a SQLAlchemy driver suffix."""
        if value.startswith("postgres://"):
            return "postgresql+psycopg://" + value.removeprefix("postgres://")
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value.removeprefix("postgresql://")
        return value

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
