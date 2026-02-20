"""MCP blade — Pydantic models."""

from __future__ import annotations

from typing import Any, Literal

from jackknife.core.models import JackknifeBaseModel


class MCPServerConfig(JackknifeBaseModel):
    """Configuration for a single MCP server connection."""

    name: str
    transport: Literal["stdio", "sse"] = "stdio"
    command: str = ""  # e.g., "npx"
    args: list[str] = []  # e.g., ["-y", "@modelcontextprotocol/server-filesystem"]
    url: str = ""  # For SSE transport
    env: dict[str, str] = {}  # Environment variables for the server process


class MCPTool(JackknifeBaseModel):
    """A tool exposed by an MCP server."""

    name: str
    description: str
    input_schema: dict[str, Any] = {}


class MCPToolResult(JackknifeBaseModel):
    """Result from calling an MCP tool."""

    tool_name: str
    content: list[dict[str, Any]] = []
    is_error: bool = False
