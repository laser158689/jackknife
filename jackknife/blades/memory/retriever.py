"""
Memory blade — semantic search retriever.

Wraps BaseMemoryStore with convenience query methods used by
context_files.py and the CLI search command.
"""

from __future__ import annotations

from typing import Any

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.blades.memory.models import MemoryEntry, SearchResult


class MemoryRetriever:
    """
    High-level query interface over a BaseMemoryStore.

    All filtering beyond the semantic query is done post-retrieval
    in Python so the store interface stays minimal.
    """

    def __init__(self, store: BaseMemoryStore) -> None:
        self._store = store

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """Semantic search with optional minimum relevance score."""
        results = await self._store.search(query, limit=limit)
        return [r for r in results if r.score >= min_score]

    async def search_by_tags(
        self,
        query: str,
        tags: list[str],
        limit: int = 10,
    ) -> list[SearchResult]:
        """Semantic search filtered to entries that carry ALL of the given tags."""
        all_results = await self._store.search(query, limit=limit * 3)
        tag_set = set(tags)
        filtered = [r for r in all_results if tag_set.issubset(set(r.entry.tags))]
        return filtered[:limit]

    async def search_by_type(
        self,
        query: str,
        entry_type: str,
        limit: int = 10,
    ) -> list[SearchResult]:
        """Semantic search filtered to a specific entry type."""
        results = await self._store.search(
            query,
            limit=limit,
            filters={"entry_type": entry_type},
        )
        return results

    async def get_context_entries(
        self,
        types: list[str] | None = None,
    ) -> list[MemoryEntry]:
        """
        Return all entries of context-relevant types.

        Used by context_files.py to generate dev tool files.
        Defaults to architecture, decision, convention, and context entries.
        """
        if types is None:
            types = ["architecture", "decision", "convention", "context"]

        results: list[SearchResult] = []
        seen: set[str] = set()

        for entry_type in types:
            hits = await self._store.search(
                "project architecture decisions conventions",
                limit=50,
                filters={"entry_type": entry_type},
            )
            for hit in hits:
                key = str(hit.entry.id)
                if key not in seen:
                    seen.add(key)
                    results.append(hit)

        return [r.entry for r in results]

    async def list_all_tags(self) -> list[str]:
        """Return all unique tags in the store."""
        return await self._store.list_tags()

    async def get_by_id(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a specific entry by ID."""
        return await self._store.get(entry_id)

    async def delete(self, entry_id: str) -> bool:
        """Delete an entry by ID."""
        return await self._store.delete(entry_id)

    def _entries_by_type(self, entries: list[MemoryEntry], entry_type: str) -> list[MemoryEntry]:
        return [e for e in entries if e.entry_type == entry_type]

    async def summarize(self) -> dict[str, Any]:
        """Return a summary of the memory store contents."""
        tags = await self._store.list_tags()
        return {"total_tags": len(tags), "tags": tags}
