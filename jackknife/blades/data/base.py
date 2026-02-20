"""Data blade — Protocol and ABC definitions for all data source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DataConnectorProtocol(Protocol):
    """Structural protocol shared by all data connectors."""

    async def connect(self) -> None:
        """Establish connection to the data source."""
        ...

    async def disconnect(self) -> None:
        """Close connection."""
        ...

    async def health_check(self) -> bool:
        """Check if the data source is reachable."""
        ...


class BaseDataConnector(ABC):
    """Abstract base with connect/disconnect lifecycle and async context manager."""

    _connected: bool = False

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection."""

    async def health_check(self) -> bool:
        """Default: verify connection is established."""
        return self._connected

    async def __aenter__(self) -> BaseDataConnector:
        await self.connect()
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.disconnect()


class BaseSQLConnector(BaseDataConnector):
    """ABC for SQL databases (PostgreSQL, MySQL, SQLite)."""

    @abstractmethod
    async def execute(self, query: str, params: dict[str, Any] | None = None) -> Any:
        """Execute a query and return results."""

    @abstractmethod
    async def execute_many(self, query: str, params_list: list[dict[str, Any]]) -> int:
        """Batch execute a query. Returns row count affected."""

    @abstractmethod
    async def fetch_one(
        self, query: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | None:
        """Fetch a single row."""

    @abstractmethod
    async def fetch_all(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Fetch all matching rows."""


class BaseNoSQLConnector(BaseDataConnector):
    """ABC for document stores (MongoDB)."""

    @abstractmethod
    async def insert_one(self, collection: str, document: dict[str, Any]) -> str:
        """Insert a document. Returns inserted ID."""

    @abstractmethod
    async def find_one(self, collection: str, filter: dict[str, Any]) -> dict[str, Any] | None:
        """Find a single document."""

    @abstractmethod
    async def find_many(
        self, collection: str, filter: dict[str, Any], limit: int = 100
    ) -> list[dict[str, Any]]:
        """Find multiple documents."""

    @abstractmethod
    async def update_one(
        self, collection: str, filter: dict[str, Any], update: dict[str, Any]
    ) -> bool:
        """Update a single document."""

    @abstractmethod
    async def delete_one(self, collection: str, filter: dict[str, Any]) -> bool:
        """Delete a single document."""


class BaseGraphConnector(BaseDataConnector):
    """ABC for graph databases (Neo4j)."""

    @abstractmethod
    async def run_query(
        self, cypher: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Run a Cypher query and return results."""

    @abstractmethod
    async def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node. Returns node ID."""

    @abstractmethod
    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> str:
        """Create a relationship between two nodes."""
