"""
Storage blade — AWS S3 implementation.

boto3 is synchronous. All operations run in a thread pool executor
via asyncio.get_running_loop().run_in_executor().
"""

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
    import boto3
    from botocore.exceptions import ClientError
except ImportError as exc:
    raise ImportError(
        "boto3 is not installed. Enable the storage-s3 extra: poetry install -E storage-s3"
    ) from exc

log = get_logger(__name__)


class S3FileStorage(BaseFileStorage):
    """AWS S3 storage backend."""

    def __init__(
        self,
        bucket: str,
        prefix: str = "",
        region: str = "us-east-1",
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
    ) -> None:
        self._bucket = bucket
        self._prefix = prefix.rstrip("/")
        kwargs: dict[str, Any] = {"region_name": region}
        if aws_access_key_id:
            kwargs["aws_access_key_id"] = aws_access_key_id
        if aws_secret_access_key:
            kwargs["aws_secret_access_key"] = aws_secret_access_key
        self._s3 = boto3.client("s3", **kwargs)

    def _key(self, uri: str) -> str:
        return f"{self._prefix}/{uri}".lstrip("/") if self._prefix else uri

    async def _run(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(fn, *args, **kwargs))

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        key = self._key(destination)
        try:
            if isinstance(source, Path):
                await self._run(self._s3.upload_file, str(source), self._bucket, key)
                size = source.stat().st_size
            else:
                data = source.read()
                await self._run(self._s3.put_object, Bucket=self._bucket, Key=key, Body=data)
                size = len(data)
        except ClientError as exc:
            raise StorageConnectionError(f"S3 upload failed: {exc}") from exc
        uri = f"s3://{self._bucket}/{key}"
        log.info("s3_uploaded", uri=uri, size_bytes=size)
        return UploadResult(uri=uri, backend="s3", size_bytes=size)

    async def download(self, source_uri: str, destination: Path) -> Path:
        key = self._key(source_uri.removeprefix(f"s3://{self._bucket}/"))
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            await self._run(self._s3.download_file, self._bucket, key, str(destination))
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                raise StorageNotFoundError(f"Not found: {source_uri!r}") from exc
            raise StorageConnectionError(f"S3 download failed: {exc}") from exc
        return destination

    async def delete(self, uri: str) -> bool:
        key = self._key(uri)
        try:
            await self._run(self._s3.delete_object, Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    async def exists(self, uri: str) -> bool:
        key = self._key(uri)
        try:
            await self._run(self._s3.head_object, Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    async def get_metadata(self, uri: str) -> FileMetadata:
        key = self._key(uri)
        try:
            resp = await self._run(self._s3.head_object, Bucket=self._bucket, Key=key)
        except ClientError as exc:
            raise StorageNotFoundError(f"Not found: {uri!r}") from exc
        last_mod: datetime | None = resp.get("LastModified")
        return FileMetadata(
            uri=f"s3://{self._bucket}/{key}",
            name=Path(key).name,
            size_bytes=resp.get("ContentLength", 0),
            content_type=resp.get("ContentType"),
            last_modified=last_mod.replace(tzinfo=UTC) if last_mod else None,
        )

    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        full_prefix = self._key(prefix)
        try:
            paginator = self._s3.get_paginator("list_objects_v2")
            pages = await self._run(
                paginator.paginate,
                Bucket=self._bucket,
                Prefix=full_prefix,
                Delimiter="" if recursive else "/",
            )
        except ClientError as exc:
            raise StorageConnectionError(f"S3 list failed: {exc}") from exc

        items: list[FileMetadata] = []
        for page in pages:
            for obj in page.get("Contents", []):
                last_mod = obj.get("LastModified")
                items.append(
                    FileMetadata(
                        uri=f"s3://{self._bucket}/{obj['Key']}",
                        name=Path(obj["Key"]).name,
                        size_bytes=obj.get("Size", 0),
                        last_modified=last_mod.replace(tzinfo=UTC) if last_mod else None,
                    )
                )
        return items
