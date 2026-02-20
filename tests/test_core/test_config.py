"""Tests for the configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest

from jackknife.core.config import get_settings, validate_config_on_startup


def test_default_settings_load() -> None:
    """Settings should load with defaults when no env vars are set."""
    settings = get_settings()
    assert settings.llm.provider == "openai"
    assert settings.llm.model == "gpt-4o-mini"
    assert settings.memory.collection == "project_memory"
    assert settings.storage.backend == "local"


def test_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables override defaults."""
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.llm.provider == "anthropic"


def test_memory_persist_dir_must_be_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Relative paths in memory.persist_dir should raise ValidationError."""
    from pydantic import ValidationError as PydanticValidationError

    monkeypatch.setenv("MEMORY_PERSIST_DIR", "../relative/path")
    get_settings.cache_clear()
    with pytest.raises(PydanticValidationError, match="absolute path"):
        get_settings()


def test_storage_base_path_must_be_absolute(monkeypatch: pytest.MonkeyPatch) -> None:
    """Relative paths in storage.base_path should raise ValidationError."""
    from pydantic import ValidationError as PydanticValidationError

    monkeypatch.setenv("STORAGE_BASE_PATH", "relative/path")
    get_settings.cache_clear()
    with pytest.raises(PydanticValidationError, match="absolute path"):
        get_settings()


def test_absolute_paths_are_accepted(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Absolute paths should pass validation."""
    monkeypatch.setenv("MEMORY_PERSIST_DIR", str(tmp_path / "memory"))
    monkeypatch.setenv("STORAGE_BASE_PATH", str(tmp_path / "storage"))
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.memory.persist_dir == str(tmp_path / "memory")


def test_validate_config_on_startup_passes_with_valid_config(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("MEMORY_PERSIST_DIR", str(tmp_path / "memory"))
    get_settings.cache_clear()
    settings = get_settings()
    # Should not raise
    validate_config_on_startup(settings)


def test_settings_are_cached() -> None:
    """get_settings() should return the same object on repeated calls."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
