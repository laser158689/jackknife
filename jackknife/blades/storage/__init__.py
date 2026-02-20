"""Storage blade — local and cloud file storage."""

from jackknife.blades.storage.base import BaseFileStorage, FileStorageProtocol
from jackknife.blades.storage.factory import create_storage
from jackknife.blades.storage.models import FileMetadata, UploadResult

__all__ = [
    "BaseFileStorage",
    "FileStorageProtocol",
    "create_storage",
    "FileMetadata",
    "UploadResult",
]
