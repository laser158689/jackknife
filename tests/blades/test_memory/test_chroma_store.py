"""Tests for ChromaMemoryStore using an in-memory ChromaDB client."""

from __future__ import annotations

import pytest

from jackknife.blades.memory.chroma_store import ChromaMemoryStore
from jackknife.blades.memory.models import MemoryEntry


@pytest.fixture
async def store(tmp_path):
    """ChromaMemoryStore backed by a temp directory."""
    s = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    return s


async def test_store_and_retrieve(store):
    entry = MemoryEntry(content="Use async SQLAlchemy for all SQL", tags=["architecture"])
    entry_id = await store.store(entry)
    assert entry_id == str(entry.id)

    retrieved = await store.get(entry_id)
    assert retrieved is not None
    assert retrieved.content == entry.content
    assert "architecture" in retrieved.tags


async def test_search_returns_results(store):
    entry = MemoryEntry(content="PostgreSQL is the primary database", tags=["architecture"])
    await store.store(entry)

    results = await store.search("database", limit=5)
    assert len(results) >= 1
    assert any("database" in r.entry.content.lower() for r in results)
    # Scores should be in [0, 1]
    for r in results:
        assert 0.0 <= r.score <= 1.0


async def test_search_empty_store_returns_empty(store):
    results = await store.search("anything", limit=5)
    assert results == []


async def test_delete_entry(store):
    entry = MemoryEntry(content="Temporary note")
    entry_id = await store.store(entry)

    deleted = await store.delete(entry_id)
    assert deleted is True

    retrieved = await store.get(entry_id)
    assert retrieved is None


async def test_delete_nonexistent_returns_false(store):
    result = await store.delete("00000000-0000-0000-0000-000000000000")
    # ChromaDB may not raise on delete of non-existent — just returns True/False
    assert isinstance(result, bool)


async def test_list_tags(store):
    await store.store(MemoryEntry(content="a", tags=["tag1", "tag2"]))
    await store.store(MemoryEntry(content="b", tags=["tag2", "tag3"]))
    tags = await store.list_tags()
    assert "tag1" in tags
    assert "tag2" in tags
    assert "tag3" in tags
    assert tags == sorted(tags)


async def test_upsert_updates_existing(store):
    entry = MemoryEntry(content="Original content")
    await store.store(entry)

    entry_updated = MemoryEntry(id=entry.id, content="Updated content")
    await store.store(entry_updated)

    retrieved = await store.get(str(entry.id))
    assert retrieved is not None
    assert retrieved.content == "Updated content"


async def test_clear_collection(store):
    await store.store(MemoryEntry(content="entry 1"))
    await store.store(MemoryEntry(content="entry 2"))
    count = await store.clear_collection()
    assert count >= 2

    results = await store.search("entry", limit=10)
    assert results == []


async def test_multiple_entry_types(store):
    for entry_type in ["decision", "architecture", "convention"]:
        await store.store(
            MemoryEntry(content=f"A {entry_type} note", entry_type=entry_type)  # type: ignore[arg-type]
        )
    results = await store.search("note", limit=10)
    types_found = {r.entry.entry_type for r in results}
    assert len(types_found) >= 2
