"""Tests for updated factory functions."""

from __future__ import annotations

import pytest

from jackknife.blades.agents.factory import create_echo_worker, create_orchestrator
from jackknife.blades.llm.factory import create_llm
from jackknife.blades.mcp.factory import create_registry
from jackknife.blades.memory.factory import create_memory_store
from jackknife.blades.storage.factory import create_storage
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError


def test_memory_factory_raises_without_persist_dir(test_settings: Settings) -> None:
    """create_memory_store raises ConfigurationError when persist_dir is empty."""
    import os

    os.environ.pop("MEMORY_PERSIST_DIR", None)
    from jackknife.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    get_settings.cache_clear()
    if not settings.memory.persist_dir:
        with pytest.raises(ConfigurationError, match="MEMORY_PERSIST_DIR"):
            create_memory_store(settings)


def test_memory_factory_returns_store(test_settings: Settings) -> None:
    from jackknife.blades.memory.chroma_store import ChromaMemoryStore

    store = create_memory_store(test_settings)
    assert isinstance(store, ChromaMemoryStore)


def test_llm_factory_raises_for_unknown_provider(test_settings: Settings) -> None:
    # Create settings with unknown provider
    import os

    os.environ["LLM_PROVIDER"] = "unknown_provider"
    from jackknife.core.config import get_settings

    get_settings.cache_clear()
    settings = get_settings()
    get_settings.cache_clear()
    os.environ.pop("LLM_PROVIDER", None)
    with pytest.raises(ConfigurationError, match="Unknown LLM provider"):
        create_llm(settings)


def test_storage_factory_returns_local(test_settings: Settings) -> None:
    from jackknife.blades.storage.local import LocalFileStorage

    storage = create_storage(test_settings)
    assert isinstance(storage, LocalFileStorage)


def test_orchestrator_factory() -> None:
    orch = create_orchestrator(max_parallel=2)
    assert orch._max_parallel == 2


def test_echo_worker_factory() -> None:
    worker = create_echo_worker()
    assert worker.name == "echo_worker"


def test_registry_factory_returns_registry() -> None:
    from jackknife.blades.mcp.registry import MCPRegistry

    reg = create_registry()
    assert isinstance(reg, MCPRegistry)
