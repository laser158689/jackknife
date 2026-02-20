"""
Memory blade — ChromaDB implementation.

ChromaDB is synchronous. Every operation is wrapped with
asyncio.get_running_loop().run_in_executor() to avoid blocking
the event loop. Multiple agents can call search() concurrently;
writes must be serialized through MemoryWriteQueue.
"""

from __future__ import annotations

import asyncio
from functools import partial
from pathlib import Path
from typing import Any
from uuid import UUID

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.blades.memory.models import MemoryEntry, SearchResult
from jackknife.core.exceptions import MemorySearchError, MemoryWriteError
from jackknife.core.logging import get_logger

try:
    import chromadb
    from chromadb import Collection
except ImportError as exc:
    raise ImportError(
        "ChromaDB is not installed. Enable the memory extra: poetry install -E memory"
    ) from exc

log = get_logger(__name__)

_VALID_ENTRY_TYPES = {
    "general",
    "decision",
    "architecture",
    "convention",
    "error",
    "fix",
    "context",
}


class ChromaMemoryStore(BaseMemoryStore):
    """
    ChromaDB-backed memory store.

    Concurrent reads are safe. Concurrent writes MUST be serialized through
    MemoryWriteQueue (write_queue.py).

    Args:
        persist_dir: Absolute path to the ChromaDB persistence directory.
        collection_name: Name of the ChromaDB collection.
    """

    def __init__(
        self,
        persist_dir: str,
        collection_name: str = "project_memory",
    ) -> None:
        Path(persist_dir).mkdir(parents=True, exist_ok=True)
        self._persist_dir = persist_dir
        self._collection_name = collection_name
        self._client: chromadb.PersistentClient | None = None
        self._collection: Collection | None = None

    # ── Private helpers ──────────────────────────────────────────────────────

    def _client_sync(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self._persist_dir)
        return self._client

    def _collection_sync(self) -> Collection:
        if self._collection is None:
            self._collection = self._client_sync().get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    def _to_metadata(self, entry: MemoryEntry) -> dict[str, str]:
        meta: dict[str, str] = {
            "tags": ",".join(entry.tags),
            "source": entry.source or "",
            "entry_type": entry.entry_type,
            "created_at": entry.created_at.isoformat(),
        }
        for k, v in entry.metadata.items():
            if isinstance(v, str):
                meta[f"ext_{k}"] = v
        return meta

    def _from_row(self, doc_id: str, content: str, meta: dict[str, Any]) -> MemoryEntry:
        tags = [t for t in meta.get("tags", "").split(",") if t]
        source = meta.get("source") or None
        raw_type = meta.get("entry_type", "general")
        entry_type = raw_type if raw_type in _VALID_ENTRY_TYPES else "general"
        extra = {k[4:]: v for k, v in meta.items() if k.startswith("ext_")}
        return MemoryEntry.model_validate(
            {
                "id": UUID(doc_id),
                "content": content,
                "tags": tags,
                "source": source,
                "entry_type": entry_type,
                "metadata": extra,
            }
        )

    # ── BaseMemoryStore interface ─────────────────────────────────────────────

    async def store(self, entry: MemoryEntry) -> str:
        doc_id = str(entry.id)
        col = self._collection_sync()
        try:
            await self._run(
                col.upsert,
                ids=[doc_id],
                documents=[entry.content],
                metadatas=[self._to_metadata(entry)],
            )
            log.debug("memory_stored", entry_id=doc_id, entry_type=entry.entry_type)
            return doc_id
        except Exception as exc:
            raise MemoryWriteError(f"Failed to store entry {doc_id}: {exc}") from exc

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        col = self._collection_sync()
        try:
            count: int = await self._run(col.count)
            if count == 0:
                return []
            n_results = min(limit, count)
            results: dict[str, Any] = await self._run(
                col.query,
                query_texts=[query],
                n_results=n_results,
                where=filters,
            )
        except Exception as exc:
            raise MemorySearchError(f"Search failed for {query!r}: {exc}") from exc

        ids: list[str] = (results.get("ids") or [[]])[0]
        documents: list[str] = (results.get("documents") or [[]])[0]
        metadatas: list[dict[str, Any]] = (results.get("metadatas") or [[]])[0]
        distances: list[float] = (results.get("distances") or [[]])[0]

        out: list[SearchResult] = []
        for i, doc_id in enumerate(ids):
            content = documents[i] if i < len(documents) else ""
            meta: dict[str, Any] = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0
            score = max(0.0, 1.0 - dist)
            entry = self._from_row(doc_id, content, meta)
            out.append(SearchResult(entry=entry, score=score, distance=dist))
        return out

    async def get(self, entry_id: str) -> MemoryEntry | None:
        col = self._collection_sync()
        try:
            result: dict[str, Any] = await self._run(
                col.get, ids=[entry_id], include=["documents", "metadatas"]
            )
        except Exception:
            return None
        ids: list[str] = result.get("ids") or []
        if not ids:
            return None
        documents: list[str] = result.get("documents") or []
        metadatas: list[dict[str, Any]] = result.get("metadatas") or []
        content = documents[0] if documents else ""
        meta: dict[str, Any] = metadatas[0] if metadatas else {}
        return self._from_row(entry_id, content, meta)

    async def delete(self, entry_id: str) -> bool:
        col = self._collection_sync()
        try:
            await self._run(col.delete, ids=[entry_id])
            return True
        except Exception:
            return False

    async def list_tags(self) -> list[str]:
        col = self._collection_sync()
        try:
            result: dict[str, Any] = await self._run(col.get, include=["metadatas"])
        except Exception:
            return []
        tags: set[str] = set()
        for meta in result.get("metadatas") or []:
            for tag in meta.get("tags", "").split(","):
                if tag:
                    tags.add(tag)
        return sorted(tags)

    async def clear_collection(self) -> int:
        col = self._collection_sync()
        count: int = await self._run(col.count)
        client = self._client_sync()
        await self._run(client.delete_collection, self._collection_name)
        self._collection = None
        log.info("memory_collection_cleared", count=count)
        return count
