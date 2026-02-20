"""Memory blade — factory function."""

from __future__ import annotations

from jackknife.blades.memory.base import BaseMemoryStore
from jackknife.core.config import Settings


def create_memory_store(settings: Settings) -> BaseMemoryStore:
    """
    Create a memory store from settings.

    Phase 2 will wire in the ChromaDB implementation.

    Args:
        settings: Application settings (uses settings.memory)

    Returns:
        A BaseMemoryStore implementation
    """
    # Phase 2: wire in ChromaDB store
    raise NotImplementedError(
        "Memory blade implementation coming in Phase 2. "
        "Interface is defined — see jackknife/blades/memory/base.py"
    )
