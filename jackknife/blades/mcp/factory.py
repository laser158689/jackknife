"""MCP blade — factory function."""

from __future__ import annotations

from jackknife.blades.mcp.base import BaseMCPClient
from jackknife.blades.mcp.models import MCPServerConfig


def create_mcp_client(config: MCPServerConfig) -> BaseMCPClient:
    """
    Create an MCP client for a given server config.

    Phase 2 will wire in the Anthropic mcp SDK client.
    """
    raise NotImplementedError(
        "MCP client implementation coming in Phase 2. "
        "Interface is defined — see jackknife/blades/mcp/base.py"
    )
