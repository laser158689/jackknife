"""Tests for the MCP blade Protocol and ABC."""

from __future__ import annotations

from typing import Any

from jackknife.blades.mcp.base import BaseMCPClient, MCPClientProtocol
from jackknife.blades.mcp.models import MCPServerConfig, MCPTool, MCPToolResult


class MockMCPClient(BaseMCPClient):
    """Minimal mock MCP client for testing the interface."""

    def __init__(self) -> None:
        self._connected = False

    async def connect(self, config: MCPServerConfig) -> None:
        self._connected = True

    async def list_tools(self) -> list[MCPTool]:
        return [MCPTool(name="test_tool", description="A test tool")]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> MCPToolResult:
        return MCPToolResult(tool_name=tool_name, content=[{"text": "result"}])

    async def disconnect(self) -> None:
        self._connected = False


def test_mock_satisfies_protocol() -> None:
    mock = MockMCPClient()
    assert isinstance(mock, MCPClientProtocol)


async def test_connect_and_list_tools() -> None:
    mock = MockMCPClient()
    config = MCPServerConfig(name="test", command="echo", args=["hello"])
    await mock.connect(config)
    tools = await mock.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"


async def test_call_tool() -> None:
    mock = MockMCPClient()
    result = await mock.call_tool("test_tool", {"arg": "value"})
    assert result.tool_name == "test_tool"
    assert result.is_error is False


async def test_health_check() -> None:
    mock = MockMCPClient()
    assert await mock.health_check() is True


async def test_context_manager() -> None:
    mock = MockMCPClient()
    async with mock:
        tools = await mock.list_tools()
        assert len(tools) == 1


def test_server_config_model() -> None:
    config = MCPServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
    )
    assert config.name == "filesystem"
    assert config.transport == "stdio"
    assert len(config.args) == 3


def test_factory_creates_client() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient
    from jackknife.blades.mcp.factory import create_mcp_client

    client = create_mcp_client()
    assert isinstance(client, MCPStdioClient)
