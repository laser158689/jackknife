"""Tests for the storage factory — S3, GCS, Azure, and error paths."""

from __future__ import annotations

import sys
import types
from pathlib import Path
from typing import Literal
from unittest.mock import MagicMock, patch

import pytest

from jackknife.core.config import Settings, StorageSettings
from jackknife.core.exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings(
    backend: Literal["local", "s3", "gcs", "azure"],
    bucket: str = "",
    region: str = "us-east-1",
) -> Settings:
    """Build a Settings object with a specific storage backend."""
    settings = Settings()
    settings.storage = StorageSettings(backend=backend, bucket=bucket, region=region)
    return settings


def _make_s3_modules() -> dict[str, types.ModuleType]:
    """Return a minimal sys.modules patch for boto3 / botocore."""
    boto3_mod = MagicMock(name="boto3")
    botocore_mod = MagicMock(name="botocore")
    botocore_exceptions_mod = MagicMock(name="botocore.exceptions")
    botocore_exceptions_mod.ClientError = Exception
    botocore_mod.exceptions = botocore_exceptions_mod

    return {
        "boto3": boto3_mod,
        "botocore": botocore_mod,
        "botocore.exceptions": botocore_exceptions_mod,
    }


def _make_gcs_modules() -> dict[str, types.ModuleType]:
    """Return a minimal sys.modules patch for google-cloud-storage."""
    google_mod = MagicMock(name="google")
    google_cloud_mod = MagicMock(name="google.cloud")
    gcs_mod = MagicMock(name="google.cloud.storage")
    google_cloud_exceptions_mod = MagicMock(name="google.cloud.exceptions")
    google_cloud_exceptions_mod.NotFound = Exception

    google_mod.cloud = google_cloud_mod
    google_cloud_mod.storage = gcs_mod
    google_cloud_mod.exceptions = google_cloud_exceptions_mod

    return {
        "google": google_mod,
        "google.cloud": google_cloud_mod,
        "google.cloud.storage": gcs_mod,
        "google.cloud.exceptions": google_cloud_exceptions_mod,
    }


def _make_azure_modules() -> dict[str, types.ModuleType]:
    """Return a minimal sys.modules patch for azure-storage-blob."""
    azure_mod = MagicMock(name="azure")
    azure_core_mod = MagicMock(name="azure.core")
    azure_core_exceptions_mod = MagicMock(name="azure.core.exceptions")
    azure_core_exceptions_mod.ResourceNotFoundError = Exception
    azure_storage_mod = MagicMock(name="azure.storage")
    azure_storage_blob_mod = MagicMock(name="azure.storage.blob")

    azure_mod.core = azure_core_mod
    azure_mod.storage = azure_storage_mod
    azure_core_mod.exceptions = azure_core_exceptions_mod
    azure_storage_mod.blob = azure_storage_blob_mod

    return {
        "azure": azure_mod,
        "azure.core": azure_core_mod,
        "azure.core.exceptions": azure_core_exceptions_mod,
        "azure.storage": azure_storage_mod,
        "azure.storage.blob": azure_storage_blob_mod,
    }


# ---------------------------------------------------------------------------
# Unknown backend
# ---------------------------------------------------------------------------


def test_unknown_backend_raises_configuration_error() -> None:
    """An unsupported backend string must raise ConfigurationError."""
    from jackknife.blades.storage.factory import create_storage

    settings = Settings()
    # Bypass Literal validation by assigning directly
    storage_settings = MagicMock()
    storage_settings.backend = "badbackend"
    settings.storage = storage_settings

    with pytest.raises(ConfigurationError, match="Unknown storage backend"):
        create_storage(settings)


# ---------------------------------------------------------------------------
# Local backend (no extra dependencies)
# ---------------------------------------------------------------------------


def test_factory_local_no_base_path() -> None:
    """Local backend uses '.' when base_path is empty."""
    from jackknife.blades.storage.factory import create_storage
    from jackknife.blades.storage.local import LocalFileStorage

    settings = _settings("local", bucket="")
    storage = create_storage(settings)
    assert isinstance(storage, LocalFileStorage)


def test_factory_local_with_base_path(tmp_path: Path) -> None:
    """Local backend respects an explicit absolute base_path."""
    from jackknife.blades.storage.factory import create_storage
    from jackknife.blades.storage.local import LocalFileStorage

    settings = Settings()
    settings.storage = StorageSettings(backend="local", base_path=str(tmp_path))
    storage = create_storage(settings)
    assert isinstance(storage, LocalFileStorage)


# ---------------------------------------------------------------------------
# S3 backend
# ---------------------------------------------------------------------------


def test_factory_s3_missing_bucket_raises() -> None:
    """S3 backend without a bucket must raise ConfigurationError."""
    s3_mocks = _make_s3_modules()

    # Remove any cached s3 blade module so fresh import picks up the mock
    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.s3" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, s3_mocks):
        from jackknife.blades.storage.factory import create_storage

        settings = _settings("s3", bucket="")
        with pytest.raises(ConfigurationError, match="STORAGE_BUCKET must be set for S3"):
            create_storage(settings)


def test_factory_s3_returns_s3_storage() -> None:
    """S3 backend with a bucket returns an S3FileStorage instance."""
    s3_mocks = _make_s3_modules()

    # Evict cached modules
    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.s3" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, s3_mocks):
        # Patch the s3 blade module at the factory import level
        mock_s3_storage_instance = MagicMock(name="S3FileStorage_instance")
        mock_s3_storage_cls = MagicMock(name="S3FileStorage", return_value=mock_s3_storage_instance)
        mock_s3_module = MagicMock()
        mock_s3_module.S3FileStorage = mock_s3_storage_cls

        with patch.dict(sys.modules, {"jackknife.blades.storage.s3": mock_s3_module}):
            # Force re-import path by removing factory from cache
            import importlib

            from jackknife.blades.storage import factory

            importlib.reload(factory)

            settings = _settings("s3", bucket="my-bucket", region="eu-west-1")
            result = factory.create_storage(settings)

        assert result is mock_s3_storage_instance
        mock_s3_storage_cls.assert_called_once_with(bucket="my-bucket", region="eu-west-1")


# ---------------------------------------------------------------------------
# GCS backend
# ---------------------------------------------------------------------------


def test_factory_gcs_missing_bucket_raises() -> None:
    """GCS backend without a bucket must raise ConfigurationError."""
    gcs_mocks = _make_gcs_modules()

    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.gcs" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, gcs_mocks):
        from jackknife.blades.storage.factory import create_storage

        settings = _settings("gcs", bucket="")
        with pytest.raises(ConfigurationError, match="STORAGE_BUCKET must be set for GCS"):
            create_storage(settings)


def test_factory_gcs_returns_gcs_storage() -> None:
    """GCS backend with a bucket returns a GCSFileStorage instance."""
    gcs_mocks = _make_gcs_modules()

    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.gcs" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, gcs_mocks):
        mock_gcs_storage_instance = MagicMock(name="GCSFileStorage_instance")
        mock_gcs_storage_cls = MagicMock(
            name="GCSFileStorage", return_value=mock_gcs_storage_instance
        )
        mock_gcs_module = MagicMock()
        mock_gcs_module.GCSFileStorage = mock_gcs_storage_cls

        with patch.dict(sys.modules, {"jackknife.blades.storage.gcs": mock_gcs_module}):
            import importlib

            from jackknife.blades.storage import factory

            importlib.reload(factory)

            settings = _settings("gcs", bucket="my-gcs-bucket")
            result = factory.create_storage(settings)

        assert result is mock_gcs_storage_instance
        mock_gcs_storage_cls.assert_called_once_with(bucket="my-gcs-bucket")


# ---------------------------------------------------------------------------
# Azure backend
# ---------------------------------------------------------------------------


def test_factory_azure_missing_bucket_raises() -> None:
    """Azure backend without a container name must raise ConfigurationError."""
    azure_mocks = _make_azure_modules()

    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.azure" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, azure_mocks):
        from jackknife.blades.storage.factory import create_storage

        settings = _settings("azure", bucket="")
        with pytest.raises(ConfigurationError, match="STORAGE_BUCKET.*container name"):
            create_storage(settings)


def test_factory_azure_returns_azure_storage() -> None:
    """Azure backend with a container returns an AzureFileStorage instance."""
    azure_mocks = _make_azure_modules()

    for key in list(sys.modules.keys()):
        if "jackknife.blades.storage.azure" in key:
            del sys.modules[key]

    with patch.dict(sys.modules, azure_mocks):
        mock_azure_storage_instance = MagicMock(name="AzureFileStorage_instance")
        mock_azure_storage_cls = MagicMock(
            name="AzureFileStorage", return_value=mock_azure_storage_instance
        )
        mock_azure_module = MagicMock()
        mock_azure_module.AzureFileStorage = mock_azure_storage_cls

        with patch.dict(sys.modules, {"jackknife.blades.storage.azure": mock_azure_module}):
            import importlib

            from jackknife.blades.storage import factory

            importlib.reload(factory)

            settings = _settings("azure", bucket="my-container")
            result = factory.create_storage(settings)

        assert result is mock_azure_storage_instance
        mock_azure_storage_cls.assert_called_once_with(container="my-container")
