"""
Shared pytest fixtures for jackknife tests.

Fixtures available to all test files without explicit import
(pytest auto-discovers conftest.py).
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest

from jackknife.core.config import Settings, get_settings
from jackknife.core.config import get_settings as _get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Generator[None, None, None]:
    """Clear the lru_cache on get_settings before each test."""
    _get_settings.cache_clear()
    yield
    _get_settings.cache_clear()


@pytest.fixture
def test_settings(tmp_path: Path) -> Generator[Settings, None, None]:
    """
    Settings configured for testing.
    Uses temp directories so tests don't touch real data.
    """
    os.environ["JACKKNIFE_ENV"] = "test"
    os.environ["MEMORY_PERSIST_DIR"] = str(tmp_path / "memory_db")
    os.environ["STORAGE_BASE_PATH"] = str(tmp_path / "files")
    _get_settings.cache_clear()
    settings = get_settings()
    yield settings
    # Cleanup env vars set by this fixture
    for key in ["JACKKNIFE_ENV", "MEMORY_PERSIST_DIR", "STORAGE_BASE_PATH"]:
        os.environ.pop(key, None)


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for tests that need file I/O."""
    return tmp_path
