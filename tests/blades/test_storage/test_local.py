"""Tests for LocalFileStorage."""

from __future__ import annotations

import io

import pytest

from jackknife.blades.storage.local import LocalFileStorage
from jackknife.core.exceptions import StorageNotFoundError


@pytest.fixture
def storage(tmp_path):
    return LocalFileStorage(base_path=str(tmp_path / "storage"))


async def test_upload_from_path(storage, tmp_path):
    src = tmp_path / "input.txt"
    src.write_text("hello world")
    result = await storage.upload(src, "output.txt")
    assert result.size_bytes == len("hello world")
    assert result.backend == "local"


async def test_upload_from_binary_io(storage):
    data = b"binary content"
    result = await storage.upload(io.BytesIO(data), "binary.bin")
    assert result.size_bytes == len(data)


async def test_download_file(storage, tmp_path):
    # Upload first
    content = b"download me"
    await storage.upload(io.BytesIO(content), "myfile.bin")
    dest = tmp_path / "downloaded.bin"
    await storage.download("myfile.bin", dest)
    assert dest.read_bytes() == content


async def test_download_missing_raises(storage, tmp_path):
    with pytest.raises(StorageNotFoundError):
        await storage.download("nonexistent.txt", tmp_path / "out.txt")


async def test_exists(storage):
    assert not await storage.exists("missing.txt")
    await storage.upload(io.BytesIO(b"data"), "present.txt")
    assert await storage.exists("present.txt")


async def test_delete(storage):
    await storage.upload(io.BytesIO(b"bye"), "delete_me.txt")
    assert await storage.exists("delete_me.txt")
    deleted = await storage.delete("delete_me.txt")
    assert deleted is True
    assert not await storage.exists("delete_me.txt")


async def test_delete_missing_returns_false(storage):
    result = await storage.delete("ghost.txt")
    assert result is False


async def test_list_files(storage):
    await storage.upload(io.BytesIO(b"a"), "dir/a.txt")
    await storage.upload(io.BytesIO(b"b"), "dir/b.txt")
    items = await storage.list(recursive=True)
    assert len(items) >= 2
    names = [i.name for i in items]
    assert "a.txt" in names
    assert "b.txt" in names


async def test_get_metadata(storage):
    await storage.upload(io.BytesIO(b"metadata test"), "meta.txt")
    meta = await storage.get_metadata("meta.txt")
    assert meta.size_bytes == len(b"metadata test")
    assert meta.name == "meta.txt"
    assert meta.last_modified is not None


async def test_path_traversal_blocked(storage):
    from jackknife.core.exceptions import StorageConnectionError

    with pytest.raises(StorageConnectionError):
        await storage.exists("../../etc/passwd")
