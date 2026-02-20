"""Data blade — Pydantic models."""

from __future__ import annotations

from typing import Any, Literal

from jackknife.core.models import JackknifeBaseModel


class QueryResult(JackknifeBaseModel):
    """Generic result from a data query."""

    rows: list[dict[str, Any]] = []
    row_count: int = 0
    query: str = ""


class ConnectionConfig(JackknifeBaseModel):
    """Configuration for a data connector."""

    connector_type: Literal["sql", "mongodb", "redis", "neo4j", "csv", "excel", "parquet"]
    name: str = "default"
    extra: dict[str, Any] = {}
