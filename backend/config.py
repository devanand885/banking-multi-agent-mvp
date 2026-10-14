"""
backend/config.py
=================
Centralised application configuration loaded from environment variables.
Supports both .env files (via python-dotenv) and system environment variables.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve the project root (two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings — all values come from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ------------------------------------------------------------------ App
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ------------------------------------------------------------------ LLM
    llm_provider: Literal["gemini", "openai", "mock"] = Field(default="mock")
    gemini_api_key: str = Field(default="")
    gemini_model: str = Field(default="gemini-1.5-flash")
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o-mini")
    llm_timeout_seconds: int = Field(default=30)
    llm_max_retries: int = Field(default=2)

    # ------------------------------------------------------------------ Database
    database_url: str = Field(default=f"sqlite:///{PROJECT_ROOT / 'data' / 'banking.db'}")

    # ------------------------------------------------------------------ API
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8000)

    # ------------------------------------------------------------------ Security
    secret_key: str = Field(default="dev-secret-key-change-in-production")

    @property
    def effective_llm_provider(self) -> str:
        """Return the real provider only when a key is present, else 'mock'."""
        if self.llm_provider == "gemini" and self.gemini_api_key:
            return "gemini"
        if self.llm_provider == "openai" and self.openai_api_key:
            return "openai"
        return "mock"

    @property
    def is_mock_mode(self) -> bool:
        return self.effective_llm_provider == "mock"


# Singleton instance used throughout the application
settings = Settings()
