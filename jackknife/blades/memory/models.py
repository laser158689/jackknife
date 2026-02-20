"""Memory blade — Pydantic models."""

from __future__ import annotations

from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import Field

from jackknife.core.models import JackknifeBaseModel, TimestampedModel


class MemoryEntry(TimestampedModel):
    """A single memory entry stored in the vector store."""

    id: UUID = Field(default_factory=uuid4)
    content: str
    embedding: list[float] | None = None
    tags: list[str] = Field(default_factory=list)
    source: str | None = None  # e.g., "claude_code", "cursor", "manual", "agent"
    entry_type: Literal[
        "general", "decision", "architecture", "convention", "error", "fix", "context"
    ] = "general"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SearchResult(JackknifeBaseModel):
    """A memory search result with relevance score."""

    entry: MemoryEntry
    score: float  # Cosine similarity (higher = more relevant, 0.0–1.0)
    distance: float  # Raw ChromaDB distance (lower = more relevant)


class DevToolFiles(JackknifeBaseModel):
    """Container for all generated dev tool context files."""

    claude_md: str
    cursorrules: str
    windsurfrules: str
    agents_md: str
    copilot_instructions: str
    augment_guidelines: str
