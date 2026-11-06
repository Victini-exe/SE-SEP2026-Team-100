from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "IITM Mentoring Platform"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "dev-secret-key-change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12
    database_url: str = Field(default="sqlite:///./app.db")
    allowed_email_domains: str = "iitm.ac.in,study.iitm.ac.in"
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def allowed_domains(self) -> List[str]:
        return [item.strip().lower() for item in self.allowed_email_domains.split(",") if item.strip()]


def get_settings() -> Settings:
    env_database_url = os.getenv("DATABASE_URL")
    if env_database_url:
        return Settings(database_url=env_database_url)

    backend_root = Path(__file__).resolve().parent.parent
    default_db = backend_root / "app.db"
    return Settings(database_url=f"sqlite:///{default_db.as_posix()}")
