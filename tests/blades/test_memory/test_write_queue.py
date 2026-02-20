"""Tests for MemoryWriteQueue."""

from __future__ import annotations

from typing import Any

import pytest

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.blades.memory.models import MemoryEntry, SearchResult
from jackknife.blades.memory.write_queue import MemoryWriteQueue


class FakeStore(BaseMemoryStore):
    """In-memory store for testing the queue without ChromaDB."""

    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}

    async def store(self, entry: MemoryEntry) -> str:
        self._entries[str(entry.id)] = entry
        return str(entry.id)

    async def search(
        self, query: str, limit: int = 10, filters: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        return []

    async def get(self, entry_id: str) -> MemoryEntry | None:
        return self._entries.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        return bool(self._entries.pop(entry_id, None))

    async def list_tags(self) -> list[str]:
        return []

    async def clear_collection(self) -> int:
        count = len(self._entries)
        self._entries.clear()
        return count


@pytest.fixture
async def queue():
    store = FakeStore()
    q = MemoryWriteQueue(store)
    await q.start()
    yield q
    await q.stop()


async def test_enqueue_stores_entry(queue):
    entry = MemoryEntry(content="Test write queue entry")
    entry_id = await queue.enqueue(entry)
    assert entry_id == str(entry.id)


async def test_enqueue_multiple_entries(queue):
    entries = [MemoryEntry(content=f"entry {i}") for i in range(5)]
    ids = [await queue.enqueue(e) for e in entries]
    assert len(set(ids)) == 5


async def test_queue_serializes_concurrent_writes():
    """Multiple concurrent writes complete without error."""
    import asyncio

    store = FakeStore()
    q = MemoryWriteQueue(store)
    await q.start()
    try:
        entries = [MemoryEntry(content=f"concurrent {i}") for i in range(10)]
        results = await asyncio.gather(*[q.enqueue(e) for e in entries])
        assert len(set(results)) == 10
    finally:
        await q.stop()
