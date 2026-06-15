"""Runtime configuration, read from environment variables (prefix INSPECTOR_).

Defaults are chosen so the app boots with zero setup for local development and
tests: an on-disk SQLite database, the stub classifier (no torch download) and
the template reporter (no LLM key). Production overrides these to Postgres, the
torch backend and the Groq reporter.
"""

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

    # storage of inspection records
    database_url: str = "sqlite:///./inspector.db"
    auto_create_tables: bool = True  # set False in prod; use alembic instead

    # classifier: "torch" loads the fine-tuned ResNet-50, "stub" is deterministic
    classifier_backend: str = "stub"
    model_repo: str = "Alexissmt/solar-defect-inspector"
    model_filename: str = "solar_model.pth"
    model_cache_dir: str = ".cache"

    # report generation: "groq" calls the LLM, "template" is rule-based
    reporter_backend: str = "template"
    groq_api_key: Optional[str] = None
    groq_model: str = "llama-3.3-70b-versatile"

    # object storage for the batch ingestion pipeline
    storage_backend: str = "local"
    storage_root: str = "./data/incoming"
    gcs_bucket: Optional[str] = None
    gcs_prefix: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
