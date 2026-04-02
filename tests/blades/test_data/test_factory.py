"""Tests for the data blade factory functions."""

from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock

import pytest

from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _settings_with_sql_url(url: str = "sqlite+aiosqlite:///./test.db") -> Settings:
    settings = Settings()
    settings.sql.url = url
    return settings


def _settings_without_sql_url() -> Settings:
    settings = Settings()
    settings.sql.url = ""
    return settings


def _settings_with_mongo_uri(uri: str = "mongodb://localhost:27017") -> Settings:
    settings = Settings()
    settings.mongo.uri = uri
    return settings


def _settings_without_mongo_uri() -> Settings:
    settings = Settings()
    settings.mongo.uri = ""
    return settings


def _mock_sql_modules() -> dict[str, types.ModuleType]:
    connector_mock = MagicMock(name="SQLConnector")
    module_mock = MagicMock()
    module_mock.SQLConnector = connector_mock
    return {
        "jackknife.blades.data.sql.connector": module_mock,
    }


def _mock_mongo_modules() -> dict[str, types.ModuleType]:
    connector_mock = MagicMock(name="MongoConnector")
    module_mock = MagicMock()
    module_mock.MongoConnector = connector_mock
    return {
        "jackknife.blades.data.nosql.mongo": module_mock,
    }


def _mock_neo4j_modules() -> dict[str, types.ModuleType]:
    connector_mock = MagicMock(name="Neo4jConnector")
    module_mock = MagicMock()
    module_mock.Neo4jConnector = connector_mock
    return {
        "jackknife.blades.data.graph.neo4j": module_mock,
    }


# ---------------------------------------------------------------------------
# SQL connector
# ---------------------------------------------------------------------------


def test_create_sql_connector_raises_when_no_url() -> None:
    from jackknife.blades.data.factory import create_sql_connector

    with pytest.raises(ConfigurationError, match="DATABASE_URL"):
        create_sql_connector(_settings_without_sql_url())


def test_create_sql_connector_returns_connector() -> None:
    import importlib

    from jackknife.blades.data import factory as factory_mod

    mock_modules = _mock_sql_modules()
    with pytest.MonkeyPatch().context() as mp:
        for key, val in mock_modules.items():
            mp.setitem(sys.modules, key, val)
        # Re-import to pick up mocked modules in lazy import
        importlib.invalidate_caches()
        connector = factory_mod.create_sql_connector(_settings_with_sql_url())
    assert connector is not None


# ---------------------------------------------------------------------------
# MongoDB connector
# ---------------------------------------------------------------------------


def test_create_mongo_connector_raises_when_no_uri() -> None:
    from jackknife.blades.data.factory import create_mongo_connector

    with pytest.raises(ConfigurationError, match="MONGODB_URI"):
        create_mongo_connector(_settings_without_mongo_uri())


def test_create_mongo_connector_returns_connector() -> None:
    import importlib

    from jackknife.blades.data import factory as factory_mod

    mock_modules = _mock_mongo_modules()
    with pytest.MonkeyPatch().context() as mp:
        for key, val in mock_modules.items():
            mp.setitem(sys.modules, key, val)
        importlib.invalidate_caches()
        connector = factory_mod.create_mongo_connector(_settings_with_mongo_uri())
    assert connector is not None


# ---------------------------------------------------------------------------
# Neo4j connector
# ---------------------------------------------------------------------------


def test_create_graph_connector_returns_connector() -> None:
    import importlib

    from jackknife.blades.data import factory as factory_mod

    mock_modules = _mock_neo4j_modules()
    with pytest.MonkeyPatch().context() as mp:
        for key, val in mock_modules.items():
            mp.setitem(sys.modules, key, val)
        importlib.invalidate_caches()
        connector = factory_mod.create_graph_connector(
            uri="bolt://localhost:7687", user="neo4j", password="test"
        )
    assert connector is not None
