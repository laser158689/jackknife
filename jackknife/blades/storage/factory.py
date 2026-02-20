"""Storage blade — factory function."""

from __future__ import annotations

from jackknife.blades.storage.base import BaseFileStorage
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError

_SUPPORTED = {"local", "s3", "gcs", "azure"}


def create_storage(settings: Settings) -> BaseFileStorage:
    """
    Create a file storage backend from settings.

    Backends:
        local  — local filesystem (default, no extra required)
        s3     — AWS S3 (poetry install -E storage-s3)
        gcs    — Google Cloud Storage (poetry install -E storage-gcs)
        azure  — Azure Blob Storage (poetry install -E storage-azure)
    """
    backend = settings.storage.backend
    if backend not in _SUPPORTED:
        raise ConfigurationError(
            f"Unknown storage backend: {backend!r}. Supported: {sorted(_SUPPORTED)}"
        )

    if backend == "local":
        from jackknife.blades.storage.local import LocalFileStorage

        base_path = settings.storage.base_path or "."
        return LocalFileStorage(base_path=base_path)

    if backend == "s3":
        from jackknife.blades.storage.s3 import S3FileStorage

        if not settings.storage.bucket:
            raise ConfigurationError("STORAGE_BUCKET must be set for S3 backend")
        return S3FileStorage(bucket=settings.storage.bucket, region=settings.storage.region)

    if backend == "gcs":
        from jackknife.blades.storage.gcs import GCSFileStorage

        if not settings.storage.bucket:
            raise ConfigurationError("STORAGE_BUCKET must be set for GCS backend")
        return GCSFileStorage(bucket=settings.storage.bucket)

    from jackknife.blades.storage.azure import AzureFileStorage

    if not settings.storage.bucket:
        raise ConfigurationError("STORAGE_BUCKET (container name) must be set for Azure backend")
    return AzureFileStorage(container=settings.storage.bucket)
