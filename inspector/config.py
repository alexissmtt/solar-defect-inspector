from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="INSPECTOR_",
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    database_url: str = "sqlite:///./inspector.db"
    auto_create_tables: bool = True  # set False in prod; use alembic instead
    max_upload_bytes: int = 10 * 1024 * 1024

    classifier_backend: str = "stub"
    model_repo: str = "Alexissmt/solar-defect-inspector"
    model_filename: str = "solar_model.pth"
    model_cache_dir: str = ".cache"

    reporter_backend: str = "template"
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    storage_backend: str = "local"
    storage_root: str = "./data/incoming"
    gcs_bucket: Optional[str] = None
    gcs_prefix: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
