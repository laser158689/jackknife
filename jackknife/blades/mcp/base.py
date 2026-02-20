"""
MCP blade — Protocol and ABC definitions.

Two roles:
1. CLIENT: Connect to external MCP servers listed in jackknife.toml.
   Application code calls list_tools() / call_tool() without knowing
   which server is backing it.

2. SCAFFOLD: Generate boilerplate for new MCP servers (Phase 7).

The memory blade also exposes itself AS an MCP server (memory/mcp_server.py),
enabling any MCP-capable tool (Claude Desktop, Cursor, etc.) to read and
write shared project memory through the MCP protocol.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from jackknife.blades.mcp.models import MCPServerConfig, MCPTool, MCPToolResult


@runtime_checkable
class MCPClientProtocol(Protocol):
    """Structural protocol for MCP client implementations."""

    async def connect(self, config: MCPServerConfig) -> None:
        """Connect to an MCP server."""
        ...

    async def list_tools(self) -> list[MCPTool]:
        """List available tools from the connected server."""
        ...

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server."""
        ...

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        ...


class BaseMCPClient(ABC):
    """Abstract base class for MCP clients."""

    @abstractmethod
    async def connect(self, config: MCPServerConfig) -> None:
        """Connect to an MCP server."""

    @abstractmethod
    async def list_tools(self) -> list[MCPTool]:
        """List available tools."""

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        """Call a tool."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect."""

    async def health_check(self) -> bool:
        """Check if the server is reachable."""
        try:
            await self.list_tools()
            return True
        except Exception:
            return False

    async def __aenter__(self) -> BaseMCPClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.disconnect()
