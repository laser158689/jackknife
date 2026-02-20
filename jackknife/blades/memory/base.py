"""
Memory blade — Protocol and ABC definitions.

The memory blade is the nervous system of the multi-agent pattern.
Multiple agents (Claude Code, Cursor, Windsurf, OpenAI Codex, etc.)
share a single project memory, preventing context fragmentation.

Architecture (Phase 2 implementation):
    chroma_store.py  — ChromaDB persistence + vector search
    write_queue.py   — async queue serializing concurrent writes
    retriever.py     — semantic search with relevance filtering
    context_files.py — generates CLAUDE.md, .cursorrules, etc.
    mcp_server.py    — exposes memory as MCP server endpoint

Concurrency design:
    ChromaDB handles concurrent reads fine.
    Concurrent writes cause corruption without serialization.
    write_queue.py wraps this class to serialize all writes
    through an asyncio.Queue.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from jackknife.blades.memory.models import MemoryEntry, SearchResult


@runtime_checkable
class MemoryStoreProtocol(Protocol):
    """Structural protocol for memory stores."""

    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns the assigned ID."""
        ...

    async def search(
        self, query: str, limit: int, filters: dict[str, Any] | None
    ) -> list[SearchResult]:
        """Semantic search over stored memories."""
        ...

    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a specific memory entry by ID."""
        ...

    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry."""
        ...

    async def list_tags(self) -> list[str]:
        """List all unique tags in the memory store."""
        ...


class BaseMemoryStore(ABC):
    """
    Abstract base class for memory stores.

    Note: Do not call store() directly from concurrent contexts.
    Use MemoryWriteQueue (write_queue.py) to ensure writes are serialized.
    """

    @abstractmethod
    async def store(self, entry: MemoryEntry) -> str:
        """Store a memory entry. Returns the assigned ID."""

    @abstractmethod
    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Semantic search over stored memories."""

    @abstractmethod
    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Retrieve a specific memory entry by ID."""

    @abstractmethod
    async def delete(self, entry_id: str) -> bool:
        """Delete a memory entry. Returns True if deleted."""

    @abstractmethod
    async def list_tags(self) -> list[str]:
        """List all unique tags in the store."""

    @abstractmethod
    async def clear_collection(self) -> int:
        """Clear all entries. Returns count deleted."""

    async def health_check(self) -> bool:
        """Verify the store is accessible."""
        try:
            await self.list_tags()
            return True
        except Exception:
            return False
