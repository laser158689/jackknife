"""Data blade — factory function."""

from __future__ import annotations

from typing import Literal

from jackknife.blades.data.base import BaseDataConnector
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError

ConnectorType = Literal["sql", "mongodb", "redis", "neo4j", "csv", "excel", "parquet"]


def create_connector(connector_type: ConnectorType, settings: Settings) -> BaseDataConnector:
    """
    Create a data connector from type and settings.

    Phase 4 will wire in all connector implementations.
    """
    supported = {"sql", "mongodb", "redis", "neo4j", "csv", "excel", "parquet"}

    if connector_type not in supported:
        raise ConfigurationError(
            f"Unknown connector type: {connector_type!r}. Supported: {sorted(supported)}"
        )

    raise NotImplementedError(
        "Data blade implementation coming in Phase 4. "
        "Interface is defined — see jackknife/blades/data/base.py"
    )
