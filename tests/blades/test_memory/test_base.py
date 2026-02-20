"""Tests for the memory blade Protocol and ABC."""

from __future__ import annotations

from typing import Any

import pytest

from jackknife.blades.memory.base import BaseMemoryStore, MemoryStoreProtocol
from jackknife.blades.memory.models import MemoryEntry, SearchResult


class MockMemoryStore(BaseMemoryStore):
    """In-memory mock store for testing the interface."""

    def __init__(self) -> None:
        self._store: dict[str, MemoryEntry] = {}

    async def store(self, entry: MemoryEntry) -> str:
        entry_id = str(entry.id)
        self._store[entry_id] = entry
        return entry_id

    async def search(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        # Mock: return all entries as results with score=1.0
        results = []
        for entry in list(self._store.values())[:limit]:
            results.append(SearchResult(entry=entry, score=1.0, distance=0.0))
        return results

    async def get(self, entry_id: str) -> MemoryEntry | None:
        return self._store.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        if entry_id in self._store:
            del self._store[entry_id]
            return True
        return False

    async def list_tags(self) -> list[str]:
        tags: set[str] = set()
        for entry in self._store.values():
            tags.update(entry.tags)
        return sorted(tags)

    async def clear_collection(self) -> int:
        count = len(self._store)
        self._store.clear()
        return count


def test_mock_satisfies_protocol() -> None:
    mock = MockMemoryStore()
    assert isinstance(mock, MemoryStoreProtocol)


async def test_store_and_retrieve() -> None:
    mock = MockMemoryStore()
    entry = MemoryEntry(content="Use SQLAlchemy for async SQL", tags=["architecture"])
    entry_id = await mock.store(entry)
    retrieved = await mock.get(entry_id)
    assert retrieved is not None
    assert retrieved.content == "Use SQLAlchemy for async SQL"


async def test_delete() -> None:
    mock = MockMemoryStore()
    entry = MemoryEntry(content="Test entry")
    entry_id = await mock.store(entry)
    assert await mock.delete(entry_id) is True
    assert await mock.get(entry_id) is None


async def test_delete_nonexistent_returns_false() -> None:
    mock = MockMemoryStore()
    assert await mock.delete("nonexistent-id") is False


async def test_list_tags() -> None:
    mock = MockMemoryStore()
    await mock.store(MemoryEntry(content="A", tags=["architecture", "decision"]))
    await mock.store(MemoryEntry(content="B", tags=["convention"]))
    tags = await mock.list_tags()
    assert tags == ["architecture", "convention", "decision"]


async def test_clear_collection() -> None:
    mock = MockMemoryStore()
    for i in range(3):
        await mock.store(MemoryEntry(content=f"entry {i}"))
    count = await mock.clear_collection()
    assert count == 3
    assert await mock.list_tags() == []


async def test_health_check() -> None:
    mock = MockMemoryStore()
    assert await mock.health_check() is True


def test_factory_raises_config_error_without_persist_dir() -> None:
    from jackknife.blades.memory.factory import create_memory_store
    from jackknife.core.config import get_settings
    from jackknife.core.exceptions import ConfigurationError

    settings = get_settings()
    if not settings.memory.persist_dir:
        with pytest.raises(ConfigurationError, match="MEMORY_PERSIST_DIR"):
            create_memory_store(settings)
