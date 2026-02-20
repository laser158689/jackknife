"""
Central configuration for jackknife.

Two-layer config system:
1. jackknife.toml  — non-secret project config (committed to VCS)
2. .env            — secrets only (NEVER committed)

pydantic-settings handles .env loading automatically via BaseSettings.
Environment variables always override TOML / default values (12-factor principle).

Usage:
    from jackknife.core.config import get_settings
    settings = get_settings()
    print(settings.llm.model)
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from jackknife.core.exceptions import ConfigurationError

# ── Blade-level settings ──────────────────────────────────────────────────────


class LLMSettings(BaseSettings):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: str = Field(default="", validation_alias="LLM_API_KEY")

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")


class MemorySettings(BaseSettings):
    persist_dir: str = ""
    collection: str = "project_memory"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    @field_validator("persist_dir")
    @classmethod
    def must_be_absolute(cls, v: str) -> str:
        if v and not Path(v).is_absolute():
            raise ValueError(f"persist_dir must be an absolute path, got: {v!r}")
        return v

    model_config = SettingsConfigDict(env_prefix="MEMORY_", extra="ignore")


class StorageSettings(BaseSettings):
    backend: Literal["local", "s3", "gcs", "azure"] = "local"
    base_path: str = ""
    bucket: str = ""
    region: str = "us-east-1"

    @field_validator("base_path")
    @classmethod
    def must_be_absolute(cls, v: str) -> str:
        if v and not Path(v).is_absolute():
            raise ValueError(f"base_path must be an absolute path, got: {v!r}")
        return v

    model_config = SettingsConfigDict(env_prefix="STORAGE_", extra="ignore")


class SQLSettings(BaseSettings):
    url: str = Field(default="", validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_prefix="SQL_", extra="ignore")


class MongoSettings(BaseSettings):
    uri: str = Field(default="", validation_alias="MONGODB_URI")

    model_config = SettingsConfigDict(env_prefix="MONGO_", extra="ignore")


class RedisSettings(BaseSettings):
    url: str = Field(default="redis://localhost:6379", validation_alias="REDIS_URL")

    model_config = SettingsConfigDict(env_prefix="REDIS_", extra="ignore")


# ── Top-level settings ────────────────────────────────────────────────────────


class Settings(BaseSettings):
    """
    Top-level settings. Composes all blade settings.
    Loaded from environment variables and .env file.
    """

    env: Literal["development", "staging", "production", "test"] = "development"

    llm: LLMSettings = Field(default_factory=LLMSettings)
    memory: MemorySettings = Field(default_factory=MemorySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    sql: SQLSettings = Field(default_factory=SQLSettings)
    mongo: MongoSettings = Field(default_factory=MongoSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="JACKKNIFE_",
        case_sensitive=False,
        extra="ignore",
    )


# ── Startup validation ────────────────────────────────────────────────────────


def validate_config_on_startup(settings: Settings) -> None:
    """
    Validate critical configuration at startup.

    Raises ConfigurationError with a clear, actionable message if
    anything is misconfigured. Prevents silent failures like the
    relative-path disasters in congressus history.

    Call this in cli.py and jackknife/__init__.py.
    """
    errors: list[str] = []

    if settings.memory.persist_dir and not Path(settings.memory.persist_dir).is_absolute():
        errors.append(f"memory.persist_dir must be absolute, got: {settings.memory.persist_dir!r}")

    if settings.storage.base_path and not Path(settings.storage.base_path).is_absolute():
        errors.append(f"storage.base_path must be absolute, got: {settings.storage.base_path!r}")

    if errors:
        msg = "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        raise ConfigurationError(msg)


# ── Cached loader ─────────────────────────────────────────────────────────────


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Load and cache settings. Called once per process.

    The lru_cache ensures settings are loaded exactly once,
    making it safe to call get_settings() anywhere without
    worrying about repeated .env file reads.

    In tests, call get_settings.cache_clear() between test cases
    that need different settings.
    """
    return Settings()
