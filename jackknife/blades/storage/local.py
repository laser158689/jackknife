"""
Storage blade — local filesystem implementation.

Uses aiofiles for non-blocking I/O. Path traversal is prevented by
resolving all paths against the configured base directory.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from jackknife.blades.storage.base import BaseFileStorage
from jackknife.blades.storage.models import FileMetadata, UploadResult
from jackknife.core.exceptions import StorageConnectionError, StorageNotFoundError
from jackknife.core.logging import get_logger

try:
    import aiofiles
    import aiofiles.os
except ImportError as exc:
    raise ImportError("aiofiles is not installed. Run: poetry add aiofiles") from exc

log = get_logger(__name__)


class LocalFileStorage(BaseFileStorage):
    """
    Local filesystem storage backend.

    All paths are resolved relative to base_path. Path traversal
    (e.g. "../../../etc/passwd") is detected and rejected.
    """

    def __init__(self, base_path: str) -> None:
        self._base = Path(base_path).resolve()
        self._base.mkdir(parents=True, exist_ok=True)
        log.info("local_storage_initialized", base_path=str(self._base))

    def _resolve(self, uri: str) -> Path:
        resolved = (self._base / uri).resolve()
        if not str(resolved).startswith(str(self._base)):
            raise StorageConnectionError(f"Path traversal blocked: {uri!r}")
        return resolved

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        dest = self._resolve(destination)
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if isinstance(source, Path):
                async with aiofiles.open(source, "rb") as src:
                    data = await src.read()
            else:
                data = source.read()
            async with aiofiles.open(dest, "wb") as f:
                await f.write(data)
        except OSError as exc:
            raise StorageConnectionError(f"Upload to {destination!r} failed: {exc}") from exc

        size = dest.stat().st_size
        log.info("file_uploaded", destination=destination, size_bytes=size)
        return UploadResult(uri=str(dest), backend="local", size_bytes=size)

    async def download(self, source_uri: str, destination: Path) -> Path:
        src = self._resolve(source_uri)
        if not src.exists():
            raise StorageNotFoundError(f"File not found: {source_uri!r}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            async with aiofiles.open(src, "rb") as f:
                data = await f.read()
            async with aiofiles.open(destination, "wb") as f:
                await f.write(data)
        except OSError as exc:
            raise StorageConnectionError(f"Download of {source_uri!r} failed: {exc}") from exc
        return destination

    async def delete(self, uri: str) -> bool:
        path = self._resolve(uri)
        if not path.exists():
            return False
        try:
            await aiofiles.os.remove(path)
            return True
        except OSError:
            return False

    async def exists(self, uri: str) -> bool:
        path = self._resolve(uri)  # StorageConnectionError propagates on traversal
        try:
            return path.exists()
        except OSError:
            return False

    async def get_metadata(self, uri: str) -> FileMetadata:
        path = self._resolve(uri)
        if not path.exists():
            raise StorageNotFoundError(f"File not found: {uri!r}")
        stat = path.stat()
        return FileMetadata(
            uri=str(path),
            name=path.name,
            size_bytes=stat.st_size,
            last_modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
        )

    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        base = self._resolve(prefix) if prefix else self._base
        if not base.exists() or not base.is_dir():
            return []
        pattern = "**/*" if recursive else "*"
        items: list[FileMetadata] = []
        for path in sorted(base.glob(pattern)):
            if path.is_file():
                stat = path.stat()
                items.append(
                    FileMetadata(
                        uri=str(path),
                        name=path.name,
                        size_bytes=stat.st_size,
                        last_modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                    )
                )
        return items
