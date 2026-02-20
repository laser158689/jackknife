"""Storage blade — Azure Blob Storage implementation."""

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
    from azure.core.exceptions import ResourceNotFoundError
    from azure.storage.blob import BlobServiceClient
except ImportError as exc:
    raise ImportError(
        "azure-storage-blob is not installed. "
        "Enable the storage-azure extra: poetry install -E storage-azure"
    ) from exc

log = get_logger(__name__)


class AzureFileStorage(BaseFileStorage):
    """Azure Blob Storage backend."""

    def __init__(
        self,
        container: str,
        connection_string: str | None = None,
        account_url: str | None = None,
        prefix: str = "",
    ) -> None:
        self._container = container
        self._prefix = prefix.rstrip("/")
        if connection_string:
            client = BlobServiceClient.from_connection_string(connection_string)
        elif account_url:
            client = BlobServiceClient(account_url=account_url)
        else:
            raise StorageConnectionError("Azure storage requires connection_string or account_url")
        self._container_client = client.get_container_client(container)

    def _key(self, uri: str) -> str:
        return f"{self._prefix}/{uri}".lstrip("/") if self._prefix else uri

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        key = self._key(destination)
        blob_client = self._container_client.get_blob_client(key)
        try:
            if isinstance(source, Path):
                with open(source, "rb") as f:
                    data = f.read()
            else:
                data = source.read()
            await self._run(blob_client.upload_blob, data, overwrite=True)
        except Exception as exc:
            raise StorageConnectionError(f"Azure upload failed: {exc}") from exc
        uri = f"azure://{self._container}/{key}"
        return UploadResult(uri=uri, backend="azure", size_bytes=len(data))

    async def download(self, source_uri: str, destination: Path) -> Path:
        key = self._key(source_uri.removeprefix(f"azure://{self._container}/"))
        blob_client = self._container_client.get_blob_client(key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            stream = await self._run(blob_client.download_blob)
            data: bytes = await self._run(stream.readall)
            destination.write_bytes(data)
        except ResourceNotFoundError as exc:
            raise StorageNotFoundError(f"Not found: {source_uri!r}") from exc
        except Exception as exc:
            raise StorageConnectionError(f"Azure download failed: {exc}") from exc
        return destination

    async def delete(self, uri: str) -> bool:
        blob_client = self._container_client.get_blob_client(self._key(uri))
        try:
            await self._run(blob_client.delete_blob)
            return True
        except Exception:
            return False

    async def exists(self, uri: str) -> bool:
        blob_client = self._container_client.get_blob_client(self._key(uri))
        try:
            return bool(await self._run(blob_client.exists))
        except Exception:
            return False

    async def get_metadata(self, uri: str) -> FileMetadata:
        blob_client = self._container_client.get_blob_client(self._key(uri))
        try:
            props = await self._run(blob_client.get_blob_properties)
        except ResourceNotFoundError as exc:
            raise StorageNotFoundError(f"Not found: {uri!r}") from exc
        last_mod: datetime | None = props.get("last_modified")
        return FileMetadata(
            uri=f"azure://{self._container}/{self._key(uri)}",
            name=Path(self._key(uri)).name,
            size_bytes=props.get("size", 0),
            content_type=props.get("content_settings", {}).get("content_type"),
            last_modified=last_mod.replace(tzinfo=UTC)
            if last_mod and last_mod.tzinfo is None
            else last_mod,
        )

    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        full_prefix = self._key(prefix)
        try:
            blobs = await self._run(self._container_client.list_blobs, name_starts_with=full_prefix)
        except Exception as exc:
            raise StorageConnectionError(f"Azure list failed: {exc}") from exc
        items: list[FileMetadata] = []
        for blob in blobs:
            last_mod: datetime | None = blob.get("last_modified")
            items.append(
                FileMetadata(
                    uri=f"azure://{self._container}/{blob['name']}",
                    name=Path(blob["name"]).name,
                    size_bytes=blob.get("size", 0),
                    last_modified=last_mod.replace(tzinfo=UTC)
                    if last_mod and last_mod.tzinfo is None
                    else last_mod,
                )
            )
        return items
