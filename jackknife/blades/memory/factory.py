"""Memory blade — factory function."""

from __future__ import annotations

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError


def create_memory_store(settings: Settings) -> BaseMemoryStore:
    """
    Create a ChromaDB-backed memory store from settings.

    Requires the memory extra: poetry install -E memory
    MEMORY_PERSIST_DIR must be set to an absolute path.
    """
    from jackknife.blades.memory.chroma_store import ChromaMemoryStore

    persist_dir = settings.memory.persist_dir
    if not persist_dir:
        raise ConfigurationError(
            "MEMORY_PERSIST_DIR is not set. "
            "Set it to an absolute path in your .env file: "
            "MEMORY_PERSIST_DIR=/absolute/path/to/memory_db"
        )
    return ChromaMemoryStore(
        persist_dir=persist_dir,
        collection_name=settings.memory.collection,
    )
