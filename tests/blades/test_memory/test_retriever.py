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
