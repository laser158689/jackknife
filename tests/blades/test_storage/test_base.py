"""Tests for the storage blade Protocol and ABC."""

from __future__ import annotations

from pathlib import Path
from typing import BinaryIO

import pytest

from jackknife.blades.storage.base import BaseFileStorage, FileStorageProtocol
from jackknife.blades.storage.models import FileMetadata, UploadResult


class MockFileStorage(BaseFileStorage):
    """Minimal mock storage backend for testing the interface."""

    async def upload(self, source: Path | BinaryIO, destination: str) -> UploadResult:
        return UploadResult(uri=f"local://{destination}", backend="local", size_bytes=0)

    async def download(self, source_uri: str, destination: Path) -> Path:
        return destination

    async def delete(self, uri: str) -> bool:
        return True

    async def exists(self, uri: str) -> bool:
        return True

    async def get_metadata(self, uri: str) -> FileMetadata:
        return FileMetadata(uri=uri, name=uri.split("/")[-1])

    async def list(self, prefix: str = "", recursive: bool = True) -> list[FileMetadata]:
        return []


def test_mock_satisfies_protocol() -> None:
    mock = MockFileStorage()
    assert isinstance(mock, FileStorageProtocol)


async def test_upload_returns_result(tmp_path: Path) -> None:
    mock = MockFileStorage()
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello")
    result = await mock.upload(test_file, "uploads/test.txt")
    assert result.backend == "local"
    assert "test.txt" in result.uri


async def test_delete_returns_true() -> None:
    mock = MockFileStorage()
    assert await mock.delete("local://some/file.txt") is True


async def test_exists_returns_true() -> None:
    mock = MockFileStorage()
    assert await mock.exists("local://some/file.txt") is True


async def test_list_returns_empty() -> None:
    mock = MockFileStorage()
    result = await mock.list(prefix="")
    assert result == []


async def test_health_check_passes() -> None:
    mock = MockFileStorage()
    assert await mock.health_check() is True


def test_factory_raises_not_implemented_for_valid_backend() -> None:
    """Factory raises NotImplementedError until Phase 5 is implemented."""
    from jackknife.blades.storage.factory import create_storage
    from jackknife.core.config import get_settings

    settings = get_settings()
    with pytest.raises(NotImplementedError):
        create_storage(settings)
