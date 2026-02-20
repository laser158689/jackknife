"""Storage blade — factory function."""

from __future__ import annotations

from jackknife.blades.storage.base import BaseFileStorage
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError


def create_storage(settings: Settings) -> BaseFileStorage:
    """
    Create a file storage backend from settings.

    Phase 5 will wire in local, S3, GCS, and Azure implementations.
    """
    supported = {"local", "s3", "gcs", "azure"}

    if settings.storage.backend not in supported:
        raise ConfigurationError(
            f"Unknown storage backend: {settings.storage.backend!r}. "
            f"Supported: {sorted(supported)}"
        )

    raise NotImplementedError(
        "Storage blade implementation coming in Phase 5. "
        "Interface is defined — see jackknife/blades/storage/base.py"
    )
