"""MCP blade — consume and scaffold MCP servers."""

from jackknife.blades.mcp.base import BaseMCPClient, MCPClientProtocol
from jackknife.blades.mcp.factory import create_mcp_client
from jackknife.blades.mcp.models import MCPServerConfig, MCPTool, MCPToolResult

__all__ = [
    "MCPClientProtocol",
    "BaseMCPClient",
    "create_mcp_client",
    "MCPServerConfig",
    "MCPTool",
    "MCPToolResult",
]
