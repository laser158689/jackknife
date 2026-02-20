"""Storage blade — Protocol and ABC definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable

from jackknife.blades.storage.models import FileMetadata, UploadResult


@runtime_checkable
class FileStorageProtocol(Protocol):
    """Structural protocol for file storage backends."""

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        """Upload a file. Returns result with URI."""
        ...

    async def download(self, source_uri: str, destination: Path) -> Path:
        """Download a file to local path."""
        ...

    async def delete(self, uri: str) -> bool:
        """Delete a file. Returns True if deleted."""
        ...

    async def exists(self, uri: str) -> bool:
        """Check if a file exists."""
        ...

    async def list(self, prefix: str, recursive: bool) -> list[FileMetadata]:
        """List files with given prefix."""
        ...


class BaseFileStorage(ABC):
    """Abstract base class for file storage backends (local, S3, GCS, Azure)."""

    @abstractmethod
    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        """Upload file to storage."""

    @abstractmethod
    async def download(self, source_uri: str, destination: Path) -> Path:
        """Download file from storage."""

    @abstractmethod
    async def delete(self, uri: str) -> bool:
        """Delete file from storage."""

    @abstractmethod
    async def exists(self, uri: str) -> bool:
        """Check file existence."""

    @abstractmethod
    async def get_metadata(self, uri: str) -> FileMetadata:
        """Retrieve file metadata."""

    @abstractmethod
    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        """List files."""

    async def health_check(self) -> bool:
        """Check if storage backend is reachable."""
        try:
            await self.list(prefix="", recursive=False)
            return True
        except Exception:
            return False
