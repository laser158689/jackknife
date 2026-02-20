"""Tests for the exception hierarchy."""

import pytest

from jackknife.core.exceptions import (
    AgentError,
    ConfigurationError,
    DataConnectorError,
    GraphConnectorError,
    JackknifeError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMResponseError,
    MCPConfigError,
    MCPError,
    MCPServerError,
    MemoryError,
    MemorySearchError,
    MemoryWriteError,
    NoSQLConnectorError,
    OrchestratorError,
    ScaffoldError,
    SQLConnectorError,
    StorageConnectionError,
    StorageError,
    StorageNotFoundError,
    ValidationError,
    WorkerError,
)


def test_all_exceptions_inherit_from_jackknife_error() -> None:
    """Every exception must be catchable via JackknifeError."""
    leaf_exceptions = [
        ConfigurationError,
        ValidationError,
        LLMConnectionError,
        LLMRateLimitError,
        LLMResponseError,
        StorageConnectionError,
        StorageNotFoundError,
        MemoryWriteError,
        MemorySearchError,
        SQLConnectorError,
        NoSQLConnectorError,
        GraphConnectorError,
        MCPServerError,
        MCPConfigError,
        OrchestratorError,
        WorkerError,
        ScaffoldError,
    ]
    for exc_class in leaf_exceptions:
        assert issubclass(
            exc_class, JackknifeError
        ), f"{exc_class.__name__} must inherit from JackknifeError"


def test_llm_error_hierarchy() -> None:
    assert issubclass(LLMConnectionError, LLMError)
    assert issubclass(LLMRateLimitError, LLMError)
    assert issubclass(LLMResponseError, LLMError)
    assert issubclass(LLMError, JackknifeError)


def test_storage_error_hierarchy() -> None:
    assert issubclass(StorageConnectionError, StorageError)
    assert issubclass(StorageNotFoundError, StorageError)


def test_memory_error_hierarchy() -> None:
    assert issubclass(MemoryWriteError, MemoryError)
    assert issubclass(MemorySearchError, MemoryError)


def test_data_error_hierarchy() -> None:
    assert issubclass(SQLConnectorError, DataConnectorError)
    assert issubclass(NoSQLConnectorError, DataConnectorError)
    assert issubclass(GraphConnectorError, DataConnectorError)


def test_mcp_error_hierarchy() -> None:
    assert issubclass(MCPServerError, MCPError)
    assert issubclass(MCPConfigError, MCPError)


def test_agent_error_hierarchy() -> None:
    assert issubclass(OrchestratorError, AgentError)
    assert issubclass(WorkerError, AgentError)


def test_catch_via_base() -> None:
    """Verify you can catch all blade errors with JackknifeError."""
    for exc_class in [ConfigurationError, LLMConnectionError, MemoryWriteError, MCPServerError]:
        try:
            raise exc_class("test message")
        except JackknifeError as exc:
            assert str(exc) == "test message"
        else:
            pytest.fail(f"{exc_class.__name__} not caught by JackknifeError")
