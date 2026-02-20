"""Tests for the data blade Protocol and ABC."""

from __future__ import annotations

from typing import Any

from jackknife.blades.data.base import (
    BaseSQLConnector,
    DataConnectorProtocol,
)
from jackknife.blades.data.models import ConnectionConfig, QueryResult


class MockSQLConnector(BaseSQLConnector):
    """Minimal mock SQL connector."""

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        return None

    async def execute_many(self, query: str, params_list: list[dict[str, Any]]) -> int:
        return len(params_list)

    async def fetch_one(
        self, query: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        return {"id": 1}

    async def fetch_all(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        return [{"id": 1}]


def test_mock_sql_satisfies_protocol() -> None:
    mock = MockSQLConnector()
    assert isinstance(mock, DataConnectorProtocol)


async def test_sql_connector_lifecycle() -> None:
    mock = MockSQLConnector()
    assert mock._connected is False
    await mock.connect()
    assert mock._connected is True
    assert await mock.health_check() is True
    await mock.disconnect()
    assert mock._connected is False


async def test_sql_connector_context_manager() -> None:
    mock = MockSQLConnector()
    async with mock:
        assert mock._connected is True
    assert mock._connected is False


async def test_fetch_one() -> None:
    mock = MockSQLConnector()
    result = await mock.fetch_one("SELECT 1")
    assert result == {"id": 1}


async def test_fetch_all() -> None:
    mock = MockSQLConnector()
    results = await mock.fetch_all("SELECT * FROM table")
    assert len(results) == 1


def test_query_result_model() -> None:
    result = QueryResult(rows=[{"id": 1}], row_count=1, query="SELECT 1")
    assert result.row_count == 1
    assert len(result.rows) == 1


def test_connection_config_model() -> None:
    config = ConnectionConfig(connector_type="sql", name="primary")
    assert config.connector_type == "sql"
    assert config.name == "primary"
