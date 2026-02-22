"""Data blade — factory functions for all connector types."""

from __future__ import annotations

from jackknife.blades.data.base import BaseGraphConnector, BaseNoSQLConnector, BaseSQLConnector
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError


def create_sql_connector(settings: Settings) -> BaseSQLConnector:
    """
    Create an async SQL connector from settings.

    Requires the data-sql extra: poetry install -E data-sql
    Set DATABASE_URL in your .env file.
    """
    from jackknife.blades.data.sql.connector import SQLConnector

    if not settings.sql.url:
        raise ConfigurationError(
            "DATABASE_URL is not set. Example: DATABASE_URL=sqlite+aiosqlite:///./app.db"
        )
    return SQLConnector(url=settings.sql.url)


def create_mongo_connector(settings: Settings, database: str = "jackknife") -> BaseNoSQLConnector:
    """
    Create a MongoDB connector from settings.

    Requires the data-nosql extra: poetry install -E data-nosql
    Set MONGODB_URI in your .env file.
    """
    from jackknife.blades.data.nosql.mongo import MongoConnector

    if not settings.mongo.uri:
        raise ConfigurationError(
            "MONGODB_URI is not set. Example: MONGODB_URI=mongodb://localhost:27017"
        )
    return MongoConnector(uri=settings.mongo.uri, database=database)


def create_graph_connector(
    uri: str, user: str = "neo4j", password: str = "neo4j"
) -> BaseGraphConnector:
    """
    Create a Neo4j async connector.

    Requires the data-graph extra: poetry install -E data-graph
    """
    from jackknife.blades.data.graph.neo4j import Neo4jConnector

    return Neo4jConnector(uri=uri, user=user, password=password)
