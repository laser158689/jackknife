"""
Exception hierarchy for jackknife.

All exceptions inherit from JackknifeError. Catching JackknifeError
catches everything; catching specific subclasses gives fine-grained control.

Hierarchy:
    JackknifeError
    ├── ConfigurationError
    ├── ValidationError
    ├── LLMError
    │   ├── LLMConnectionError
    │   ├── LLMRateLimitError
    │   └── LLMResponseError
    ├── StorageError
    │   ├── StorageConnectionError
    │   └── StorageNotFoundError
    ├── MemoryError
    │   ├── MemoryWriteError
    │   └── MemorySearchError
    ├── DataConnectorError
    │   ├── SQLConnectorError
    │   ├── NoSQLConnectorError
    │   └── GraphConnectorError
    ├── MCPError
    │   ├── MCPServerError
    │   └── MCPConfigError
    ├── AgentError
    │   ├── OrchestratorError
    │   └── WorkerError
    └── ScaffoldError
"""


class JackknifeError(Exception):
    """Base exception for all jackknife errors."""


# ── Config / Validation ───────────────────────────────────────────────────────


class ConfigurationError(JackknifeError):
    """Required configuration is missing or invalid."""


class ValidationError(JackknifeError):
    """Input validation failed."""


# ── LLM blade ─────────────────────────────────────────────────────────────────


class LLMError(JackknifeError):
    """Base for LLM blade errors."""


class LLMConnectionError(LLMError):
    """Cannot connect to LLM provider."""


class LLMRateLimitError(LLMError):
    """LLM provider rate limit exceeded."""


class LLMResponseError(LLMError):
    """LLM returned an unexpected or malformed response."""


# ── Storage blade ─────────────────────────────────────────────────────────────


class StorageError(JackknifeError):
    """Base for file storage errors."""


class StorageConnectionError(StorageError):
    """Cannot connect to storage backend."""


class StorageNotFoundError(StorageError):
    """Requested file or object not found in storage."""


# ── Memory blade ──────────────────────────────────────────────────────────────


class MemoryError(JackknifeError):
    """Base for memory blade errors."""


class MemoryWriteError(MemoryError):
    """Failed to write entry to memory store."""


class MemorySearchError(MemoryError):
    """Semantic search operation failed."""


# ── Data blade ────────────────────────────────────────────────────────────────


class DataConnectorError(JackknifeError):
    """Base for data connector errors."""


class SQLConnectorError(DataConnectorError):
    """SQL connector error."""


class NoSQLConnectorError(DataConnectorError):
    """NoSQL connector error."""


class GraphConnectorError(DataConnectorError):
    """Graph database connector error."""


# ── MCP blade ─────────────────────────────────────────────────────────────────


class MCPError(JackknifeError):
    """Base for MCP blade errors."""


class MCPServerError(MCPError):
    """MCP server connection or communication error."""


class MCPConfigError(MCPError):
    """MCP server configuration is invalid."""


# ── Agent blade ───────────────────────────────────────────────────────────────


class AgentError(JackknifeError):
    """Base for agent blade errors."""


class OrchestratorError(AgentError):
    """Orchestrator task graph error."""


class WorkerError(AgentError):
    """Worker agent execution error."""


# ── Scaffold ──────────────────────────────────────────────────────────────────


class ScaffoldError(JackknifeError):
    """Project scaffolding error."""
