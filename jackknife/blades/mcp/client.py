"""
MCP blade — stdio client implementation.

Connects to an MCP server running as a subprocess (stdio transport).
The server process is started on connect() and terminated on disconnect().

Typical usage:
    config = MCPServerConfig(name="filesystem", command="npx",
                             args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"])
    async with MCPStdioClient() as client:
        await client.connect(config)
        tools = await client.list_tools()
        result = await client.call_tool("read_file", {"path": "/tmp/test.txt"})
"""

from __future__ import annotations

from typing import Any

from jackknife.blades.mcp.base import BaseMCPClient
from jackknife.blades.mcp.models import MCPServerConfig, MCPTool, MCPToolResult
from jackknife.core.exceptions import MCPConfigError, MCPServerError
from jackknife.core.logging import get_logger

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.types import CallToolResult, ListToolsResult
except ImportError as exc:
    raise ImportError("mcp is not installed. Enable the mcp extra: poetry install -E mcp") from exc

log = get_logger(__name__)


class MCPStdioClient(BaseMCPClient):
    """
    MCP client using stdio transport.

    The server is started as a child process. Communication happens
    through stdin/stdout. Each MCPStdioClient manages one server connection.
    """

    def __init__(self) -> None:
        self._config: MCPServerConfig | None = None
        self._session: ClientSession | None = None
        self._context_stack: Any = None  # holds the async context manager

    async def connect(self, config: MCPServerConfig) -> None:
        if config.transport != "stdio":
            raise MCPConfigError(
                f"MCPStdioClient only supports stdio transport, got: {config.transport!r}"
            )
        if not config.command:
            raise MCPConfigError(f"MCP server {config.name!r} has no command configured")

        self._config = config
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args,
            env=config.env or {},
        )
        try:
            ctx = stdio_client(server_params)
            streams = await ctx.__aenter__()
            self._context_stack = ctx
            read_stream, write_stream = streams
            session = ClientSession(read_stream, write_stream)
            await session.__aenter__()
            await session.initialize()
            self._session = session
            log.info("mcp_client_connected", server=config.name, command=config.command)
        except Exception as exc:
            raise MCPServerError(f"Failed to connect to MCP server {config.name!r}: {exc}") from exc

    async def list_tools(self) -> list[MCPTool]:
        if self._session is None:
            raise MCPServerError("Not connected. Call connect() first.")
        try:
            result: ListToolsResult = await self._session.list_tools()
            return [
                MCPTool(
                    name=t.name,
                    description=t.description or "",
                    input_schema=dict(t.inputSchema) if t.inputSchema else {},
                )
                for t in result.tools
            ]
        except Exception as exc:
            raise MCPServerError(f"list_tools failed: {exc}") from exc

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        if self._session is None:
            raise MCPServerError("Not connected. Call connect() first.")
        try:
            result: CallToolResult = await self._session.call_tool(tool_name, arguments)
            content = [{"type": c.type, "text": getattr(c, "text", "")} for c in result.content]
            return MCPToolResult(
                tool_name=tool_name,
                content=content,
                is_error=bool(result.isError),
            )
        except Exception as exc:
            raise MCPServerError(f"call_tool({tool_name!r}) failed: {exc}") from exc

    async def disconnect(self) -> None:
        if self._session is not None:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
            self._session = None
        if self._context_stack is not None:
            try:
                await self._context_stack.__aexit__(None, None, None)
            except Exception:
                pass
            self._context_stack = None
        if self._config:
            log.info("mcp_client_disconnected", server=self._config.name)
