"""Data blade — Neo4j async graph connector."""

from __future__ import annotations

from typing import Any

from jackknife.blades.data.base import BaseGraphConnector
from jackknife.core.exceptions import GraphConnectorError
from jackknife.core.logging import get_logger

try:
    from neo4j import AsyncDriver, AsyncGraphDatabase
except ImportError as exc:
    raise ImportError(
        "neo4j is not installed. Enable the data-graph extra: poetry install -E data-graph"
    ) from exc

log = get_logger(__name__)


class Neo4jConnector(BaseGraphConnector):
    """
    Neo4j async connector using the official neo4j Python driver.

    Usage:
        async with Neo4jConnector("bolt://localhost:7687", "neo4j", "password") as g:
            node_id = await g.create_node("Person", {"name": "Alice"})
            results = await g.run_query("MATCH (p:Person) RETURN p.name AS name")
    """

    def __init__(self, uri: str, user: str = "neo4j", password: str = "neo4j") -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._driver: AsyncDriver | None = None

    async def connect(self) -> None:
        self._driver = AsyncGraphDatabase.driver(self._uri, auth=(self._user, self._password))
        await self._driver.verify_connectivity()
        self._connected = True
        log.info("neo4j_connected", uri=self._uri)

    async def disconnect(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None
        self._connected = False

    def _d(self) -> AsyncDriver:
        if self._driver is None:
            raise GraphConnectorError("Not connected. Use 'async with Neo4jConnector(...)'")
        return self._driver

    async def run_query(
        self, cypher: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return all records as dicts."""
        try:
            async with self._d().session() as session:
                result = await session.run(cypher, parameters=params or {})
                records = await result.data()
                return [dict(r) for r in records]
        except Exception as exc:
            raise GraphConnectorError(f"Cypher query failed: {exc}") from exc

    async def create_node(self, label: str, properties: dict[str, Any]) -> str:
        """Create a node and return its internal Neo4j element ID."""
        props_clause = ", ".join(f"n.{k} = ${k}" for k in properties)
        cypher = f"CREATE (n:{label}) SET {props_clause} RETURN elementId(n) AS id"
        try:
            rows = await self.run_query(cypher, properties)
            return str(rows[0]["id"])
        except Exception as exc:
            raise GraphConnectorError(f"create_node({label!r}) failed: {exc}") from exc

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        rel_type: str,
        properties: dict[str, Any] | None = None,
    ) -> str:
        props = properties or {}
        props_clause = ", ".join(f"r.{k} = ${k}" for k in props) if props else ""
        set_clause = f" SET {props_clause}" if props_clause else ""
        cypher = (
            f"MATCH (a) WHERE elementId(a) = $from_id "
            f"MATCH (b) WHERE elementId(b) = $to_id "
            f"CREATE (a)-[r:{rel_type}]->(b){set_clause} "
            f"RETURN elementId(r) AS id"
        )
        try:
            params = {"from_id": from_id, "to_id": to_id, **props}
            rows = await self.run_query(cypher, params)
            return str(rows[0]["id"])
        except Exception as exc:
            raise GraphConnectorError(f"create_relationship failed: {exc}") from exc

    async def health_check(self) -> bool:
        try:
            rows = await self.run_query("RETURN 1 AS ok")
            return rows[0].get("ok") == 1
        except Exception:
            return False
