from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NBA Analytics API"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "staging", "production"] = "development"
    database_url: str | None = None
    provider_name: str = "unconfigured"
    provider_mode: Literal["unconfigured", "synthetic-test"] = "unconfigured"
    cors_origins: list[str] = ["http://localhost:5173"]
    log_level: str = "INFO"
    request_id_header: str = "X-Request-ID"

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_prefix="NBA_",
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def validate_runtime(self) -> None:
        if self.environment == "production" and self.provider_mode == "synthetic-test":
            raise ValueError("synthetic-test provider mode cannot run in production")


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.validate_runtime()
    return settings
