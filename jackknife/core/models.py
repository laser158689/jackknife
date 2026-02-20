"""
Shared Pydantic base models used across all blades.

Blade-specific models live in jackknife/blades/<name>/models.py.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class JackknifeBaseModel(BaseModel):
    """
    Base model for all jackknife Pydantic models.

    - extra="forbid": fail fast on unexpected fields (catches config typos)
    - str_strip_whitespace: normalize string inputs automatically
    - populate_by_name: accept both field name and alias in input
    """

    model_config = ConfigDict(
        frozen=False,
        extra="forbid",
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampedModel(JackknifeBaseModel):
    """Model with automatic created_at / updated_at UTC timestamps."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class IdentifiedModel(TimestampedModel):
    """Model with a UUID primary key."""

    id: UUID = Field(default_factory=uuid4)


class Metadata(JackknifeBaseModel):
    """
    Flexible metadata container for attaching arbitrary key-value data.

    Uses extra="allow" so any additional fields are accepted.
    Blade-specific models can embed this for extensibility.
    """

    model_config = ConfigDict(extra="allow")

    source: str | None = None
    tags: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)
