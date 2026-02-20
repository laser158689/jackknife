"""Storage blade — Google Cloud Storage implementation."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import Any, BinaryIO

from jackknife.blades.storage.base import BaseFileStorage
from jackknife.blades.storage.models import FileMetadata, UploadResult
from jackknife.core.exceptions import StorageConnectionError, StorageNotFoundError
from jackknife.core.logging import get_logger

try:
    from google.cloud import storage as gcs
    from google.cloud.exceptions import NotFound
except ImportError as exc:
    raise ImportError(
        "google-cloud-storage is not installed. "
        "Enable the storage-gcs extra: poetry install -E storage-gcs"
    ) from exc

log = get_logger(__name__)


class GCSFileStorage(BaseFileStorage):
    """Google Cloud Storage backend."""

    def __init__(self, bucket: str, prefix: str = "", project: str | None = None) -> None:
        self._bucket_name = bucket
        self._prefix = prefix.rstrip("/")
        client = gcs.Client(project=project)
        self._bucket = client.bucket(bucket)

    def _key(self, uri: str) -> str:
        return f"{self._prefix}/{uri}".lstrip("/") if self._prefix else uri

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        key = self._key(destination)
        blob = self._bucket.blob(key)
        try:
            if isinstance(source, Path):
                await self._run(blob.upload_from_filename, str(source))
                size = source.stat().st_size
            else:
                data = source.read()
                await self._run(blob.upload_from_string, data)
                size = len(data)
        except Exception as exc:
            raise StorageConnectionError(f"GCS upload failed: {exc}") from exc
        uri = f"gs://{self._bucket_name}/{key}"
        return UploadResult(uri=uri, backend="gcs", size_bytes=size)

    async def download(self, source_uri: str, destination: Path) -> Path:
        key = self._key(source_uri.removeprefix(f"gs://{self._bucket_name}/"))
        blob = self._bucket.blob(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            await self._run(blob.download_to_filename, str(destination))
        except NotFound as exc:
            raise StorageNotFoundError(f"Not found: {source_uri!r}") from exc
        except Exception as exc:
            raise StorageConnectionError(f"GCS download failed: {exc}") from exc
        return destination

    async def delete(self, uri: str) -> bool:
        blob = self._bucket.blob(self._key(uri))
        try:
            await self._run(blob.delete)
            return True
        except Exception:
            return False

    async def exists(self, uri: str) -> bool:
        blob = self._bucket.blob(self._key(uri))
        try:
            return bool(await self._run(blob.exists))
        except Exception:
            return False

    async def get_metadata(self, uri: str) -> FileMetadata:
        blob = self._bucket.blob(self._key(uri))
        try:
            await self._run(blob.reload)
        except NotFound as exc:
            raise StorageNotFoundError(f"Not found: {uri!r}") from exc
        updated: datetime | None = blob.updated
        return FileMetadata(
            uri=f"gs://{self._bucket_name}/{blob.name}",
            name=Path(blob.name).name,
            size_bytes=blob.size or 0,
            content_type=blob.content_type,
            last_modified=updated.replace(tzinfo=UTC)
            if updated and updated.tzinfo is None
            else updated,
        )

    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        full_prefix = self._key(prefix)
        delimiter = "" if recursive else "/"
        try:
            blobs = await self._run(
                self._bucket.list_blobs, prefix=full_prefix, delimiter=delimiter
            )
        except Exception as exc:
            raise StorageConnectionError(f"GCS list failed: {exc}") from exc
        items: list[FileMetadata] = []
        for blob in blobs:
            updated: datetime | None = blob.updated
            items.append(
                FileMetadata(
                    uri=f"gs://{self._bucket_name}/{blob.name}",
                    name=Path(blob.name).name,
                    size_bytes=blob.size or 0,
                    content_type=blob.content_type,
                    last_modified=updated.replace(tzinfo=UTC)
                    if updated and updated.tzinfo is None
                    else updated,
                )
            )
        return items
