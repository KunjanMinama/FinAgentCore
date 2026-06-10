"""
Application configuration — loaded from environment variables via pydantic-settings.

All secrets come from .env (gitignored). Defaults are safe for local development.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings

# Repo root — useful for locating fixtures during tests
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = ROOT_DIR / "fixtures"


class Settings(BaseSettings):
    """Immutable, cached application settings."""

    # --- LLM ---
    openai_api_key: str = Field(default="", description="OpenAI API key")
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="Model for intent classification",
    )

    # --- Application ---
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")

    # --- Timeouts ---
    pipeline_timeout_seconds: float = Field(
        default=10.0,
        description="Max seconds for the full query pipeline",
    )
    llm_timeout_seconds: float = Field(
        default=8.0,
        description="Max seconds for a single LLM call",
    )

    # --- Session memory ---
    session_max_turns: int = Field(
        default=3,
        description="Number of recent user turns to keep per session",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a singleton Settings instance (cached after first call)."""
    return Settings()
