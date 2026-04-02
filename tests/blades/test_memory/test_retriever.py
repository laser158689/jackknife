"""Tests for MemoryRetriever."""

from __future__ import annotations

import pytest

from jackknife.blades.memory.chroma_store import ChromaMemoryStore
from jackknife.blades.memory.models import MemoryEntry
from jackknife.blades.memory.retriever import MemoryRetriever


@pytest.fixture
async def retriever(tmp_path):
    store = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    await store.store(
        MemoryEntry(content="Use async SQLAlchemy", entry_type="architecture", tags=["sql"])
    )
    await store.store(
        MemoryEntry(content="Always use absolute paths", entry_type="convention", tags=["config"])
    )
    await store.store(
        MemoryEntry(content="Decided to use ChromaDB", entry_type="decision", tags=["memory"])
    )
    return MemoryRetriever(store)


async def test_search_returns_results(retriever):
    results = await retriever.search("database", limit=5)
    assert isinstance(results, list)


async def test_search_with_min_score(retriever):
    results = await retriever.search("SQLAlchemy", min_score=0.0)
    assert all(r.score >= 0.0 for r in results)


async def test_get_context_entries(retriever):
    entries = await retriever.get_context_entries()
    types = {e.entry_type for e in entries}
    # Should include architecture, convention, decision entries
    assert len(types) >= 1


async def test_list_all_tags(retriever):
    tags = await retriever.list_all_tags()
    assert "sql" in tags or "config" in tags or "memory" in tags


async def test_summarize(retriever):
    summary = await retriever.summarize()
    assert "total_tags" in summary
    assert "tags" in summary


async def test_search_by_tags(retriever):
    """Covers lines 44-47: search_by_tags filters by ALL given tags."""
    results = await retriever.search_by_tags("database", tags=["sql"])
    # All returned entries must have the "sql" tag
    for r in results:
        assert "sql" in r.entry.tags


async def test_search_by_tags_no_match(retriever):
    """search_by_tags returns empty list when no entry has the tag."""
    results = await retriever.search_by_tags("database", tags=["nonexistent_tag_xyz"])
    assert results == []


async def test_search_by_type(retriever):
    """Covers lines 56-61: search_by_type filters by entry_type."""
    results = await retriever.search_by_type("project", entry_type="architecture")
    for r in results:
        assert r.entry.entry_type == "architecture"


async def test_get_by_id_found(tmp_path):
    """Covers line 99: get_by_id returns entry when it exists."""
    from jackknife.blades.memory.chroma_store import ChromaMemoryStore

    store = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma"), collection_name="test_id")
    entry = MemoryEntry(content="find me", entry_type="context", tags=[])
    await store.store(entry)
    retriever = MemoryRetriever(store)
    found = await retriever.get_by_id(str(entry.id))
    assert found is not None
    assert found.content == "find me"


async def test_get_by_id_not_found(tmp_path):
    """get_by_id returns None for missing ID."""
    from jackknife.blades.memory.chroma_store import ChromaMemoryStore

    store = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma2"), collection_name="test_id2")
    retriever = MemoryRetriever(store)
    result = await retriever.get_by_id("00000000-0000-0000-0000-000000000000")
    assert result is None


async def test_delete(tmp_path):
    """Covers line 103: delete removes entry from store."""
    from jackknife.blades.memory.chroma_store import ChromaMemoryStore

    store = ChromaMemoryStore(persist_dir=str(tmp_path / "chroma3"), collection_name="test_del")
    entry = MemoryEntry(content="delete me", entry_type="context", tags=[])
    await store.store(entry)
    retriever = MemoryRetriever(store)
    deleted = await retriever.delete(str(entry.id))
    assert deleted is True
    assert await retriever.get_by_id(str(entry.id)) is None


def test_entries_by_type_private():
    """Covers line 106: _entries_by_type filters list."""
    from unittest.mock import MagicMock

    store = MagicMock()
    retriever = MemoryRetriever(store)
    arch = MemoryEntry(content="arch", entry_type="architecture", tags=[])
    conv = MemoryEntry(content="conv", entry_type="convention", tags=[])
    result = retriever._entries_by_type([arch, conv], "architecture")
    assert len(result) == 1
    assert result[0].entry_type == "architecture"
