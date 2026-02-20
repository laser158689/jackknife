"""Storage blade — Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from jackknife.core.models import JackknifeBaseModel


class FileMetadata(JackknifeBaseModel):
    """Metadata for a stored file."""

    uri: str
    name: str
    size_bytes: int = 0
    content_type: str | None = None
    last_modified: datetime | None = None
    checksum: str | None = None
    extra: dict[str, str] = {}


class UploadResult(JackknifeBaseModel):
    """Result of an upload operation."""

    uri: str
    backend: Literal["local", "s3", "gcs", "azure"]
    size_bytes: int
    checksum: str | None = None
