"""MCP blade — factory functions."""

from __future__ import annotations

from pathlib import Path

from jackknife.blades.mcp.client import MCPStdioClient
from jackknife.blades.mcp.registry import MCPRegistry


def create_mcp_client() -> MCPStdioClient:
    """Create an MCP stdio client. Call client.connect(config) before use."""
    return MCPStdioClient()


def create_registry(config_path: str | None = None) -> MCPRegistry:
    """Load MCP server configs from jackknife.toml."""
    path = Path(config_path) if config_path else None
    return MCPRegistry(config_path=path)
