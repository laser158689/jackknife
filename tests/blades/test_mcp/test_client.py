"""Tests for MCPStdioClient using mocks (no real MCP server required)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from jackknife.blades.mcp.models import MCPServerConfig, MCPTool, MCPToolResult
from jackknife.core.exceptions import MCPConfigError, MCPServerError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_config(
    name: str = "test-server",
    command: str = "npx",
    args: list[str] | None = None,
    transport: str = "stdio",
    env: dict[str, str] | None = None,
) -> MCPServerConfig:
    return MCPServerConfig(
        name=name,
        command=command,
        args=args or [],
        transport=transport,  # type: ignore[arg-type]
        env=env or {},
    )


def _make_tool_result_item(type_: str = "text", text: str = "hello") -> MagicMock:
    item = MagicMock()
    item.type = type_
    item.text = text
    return item


def _make_list_tools_result(tools_data: list[dict[str, Any]]) -> MagicMock:
    result = MagicMock()
    tools = []
    for d in tools_data:
        t = MagicMock()
        t.name = d["name"]
        t.description = d.get("description", "")
        t.inputSchema = d.get("inputSchema", {})
        tools.append(t)
    result.tools = tools
    return result


def _make_call_tool_result(content_items: list[MagicMock], is_error: bool = False) -> MagicMock:
    result = MagicMock()
    result.content = content_items
    result.isError = is_error
    return result


def _patched_session_and_context(
    list_tools_result: MagicMock | None = None,
    call_tool_result: MagicMock | None = None,
) -> tuple[MagicMock, MagicMock]:
    """Return (mock_session, mock_ctx) with async enter/exit wired up."""
    # Session
    session = MagicMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=None)
    session.initialize = AsyncMock()
    session.list_tools = AsyncMock(return_value=list_tools_result or _make_list_tools_result([]))
    session.call_tool = AsyncMock(
        return_value=call_tool_result or _make_call_tool_result([_make_tool_result_item()])
    )

    # Context (streams)
    read_stream = MagicMock()
    write_stream = MagicMock()
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=(read_stream, write_stream))
    ctx.__aexit__ = AsyncMock(return_value=None)

    return session, ctx


# ---------------------------------------------------------------------------
# Import guard
# ---------------------------------------------------------------------------


def test_import_succeeds() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient  # noqa: F401


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


def test_initial_state() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    assert client._config is None
    assert client._session is None
    assert client._context_stack is None


# ---------------------------------------------------------------------------
# connect — validation
# ---------------------------------------------------------------------------


async def test_connect_raises_for_non_stdio_transport() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = MCPServerConfig(name="sse-server", transport="sse", url="http://localhost")
    with pytest.raises(MCPConfigError, match="stdio transport"):
        await client.connect(config)


async def test_connect_raises_when_command_is_empty() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    # command defaults to "" in MCPServerConfig
    config = MCPServerConfig(name="no-cmd")
    with pytest.raises(MCPConfigError, match="no command configured"):
        await client.connect(config)


# ---------------------------------------------------------------------------
# connect — happy path
# ---------------------------------------------------------------------------


async def test_connect_sets_session_and_config() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = _make_config()
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(config)

    assert client._config is config
    assert client._session is session
    assert client._context_stack is ctx
    session.initialize.assert_awaited_once()


async def test_connect_passes_env_to_server_params() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = _make_config(env={"MY_VAR": "value"})
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.StdioServerParameters") as mock_params,
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(config)

    mock_params.assert_called_once_with(
        command="npx",
        args=[],
        env={"MY_VAR": "value"},
    )


async def test_connect_passes_empty_dict_when_env_is_none() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    # env defaults to {} in the model; force a config with no env
    config = MCPServerConfig(name="s", command="cmd")
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.StdioServerParameters") as mock_params,
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(config)

    _, kwargs = mock_params.call_args
    assert kwargs["env"] == {}


# ---------------------------------------------------------------------------
# connect — error propagation
# ---------------------------------------------------------------------------


async def test_connect_wraps_stdio_client_exception_in_mcp_server_error() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = _make_config()

    bad_ctx = MagicMock()
    bad_ctx.__aenter__ = AsyncMock(side_effect=RuntimeError("boom"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=bad_ctx),
        pytest.raises(MCPServerError, match="Failed to connect"),
    ):
        await client.connect(config)


async def test_connect_wraps_session_initialize_exception() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = _make_config()
    session, ctx = _patched_session_and_context()
    session.initialize = AsyncMock(side_effect=OSError("pipe broke"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
        pytest.raises(MCPServerError, match="Failed to connect"),
    ):
        await client.connect(config)


# ---------------------------------------------------------------------------
# list_tools — not connected guard
# ---------------------------------------------------------------------------


async def test_list_tools_raises_when_not_connected() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    with pytest.raises(MCPServerError, match="Not connected"):
        await client.list_tools()


# ---------------------------------------------------------------------------
# list_tools — happy path
# ---------------------------------------------------------------------------


async def test_list_tools_returns_mcp_tool_list() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    tools_data = [
        {"name": "read_file", "description": "Read a file", "inputSchema": {"type": "object"}},
        {"name": "write_file", "description": "Write a file", "inputSchema": {}},
    ]
    session, ctx = _patched_session_and_context(
        list_tools_result=_make_list_tools_result(tools_data)
    )

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        tools = await client.list_tools()

    assert len(tools) == 2
    assert all(isinstance(t, MCPTool) for t in tools)
    assert tools[0].name == "read_file"
    assert tools[0].description == "Read a file"
    assert tools[0].input_schema == {"type": "object"}
    assert tools[1].name == "write_file"
    assert tools[1].input_schema == {}


async def test_list_tools_uses_empty_string_when_description_is_none() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    raw_tool = MagicMock()
    raw_tool.name = "tool_no_desc"
    raw_tool.description = None
    raw_tool.inputSchema = None

    list_result = MagicMock()
    list_result.tools = [raw_tool]
    session, ctx = _patched_session_and_context(list_tools_result=list_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        tools = await client.list_tools()

    assert tools[0].description == ""
    assert tools[0].input_schema == {}


async def test_list_tools_uses_empty_schema_when_input_schema_is_none() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    raw_tool = MagicMock()
    raw_tool.name = "no_schema_tool"
    raw_tool.description = "A tool"
    raw_tool.inputSchema = None

    list_result = MagicMock()
    list_result.tools = [raw_tool]
    session, ctx = _patched_session_and_context(list_tools_result=list_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        tools = await client.list_tools()

    assert tools[0].input_schema == {}


# ---------------------------------------------------------------------------
# list_tools — error propagation
# ---------------------------------------------------------------------------


async def test_list_tools_wraps_session_exception_in_mcp_server_error() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    session.list_tools = AsyncMock(side_effect=RuntimeError("network error"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        with pytest.raises(MCPServerError, match="list_tools failed"):
            await client.list_tools()


# ---------------------------------------------------------------------------
# call_tool — not connected guard
# ---------------------------------------------------------------------------


async def test_call_tool_raises_when_not_connected() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    with pytest.raises(MCPServerError, match="Not connected"):
        await client.call_tool("any_tool", {})


# ---------------------------------------------------------------------------
# call_tool — happy path
# ---------------------------------------------------------------------------


async def test_call_tool_returns_mcp_tool_result() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    content_item = _make_tool_result_item(type_="text", text="file contents here")
    raw_result = _make_call_tool_result([content_item], is_error=False)
    session, ctx = _patched_session_and_context(call_tool_result=raw_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        result = await client.call_tool("read_file", {"path": "/tmp/f.txt"})

    assert isinstance(result, MCPToolResult)
    assert result.tool_name == "read_file"
    assert result.is_error is False
    assert result.content == [{"type": "text", "text": "file contents here"}]
    session.call_tool.assert_awaited_once_with("read_file", {"path": "/tmp/f.txt"})


async def test_call_tool_returns_is_error_true_when_server_signals_error() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    item = _make_tool_result_item(text="something went wrong")
    raw_result = _make_call_tool_result([item], is_error=True)
    session, ctx = _patched_session_and_context(call_tool_result=raw_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        result = await client.call_tool("failing_tool", {})

    assert result.is_error is True
    assert result.tool_name == "failing_tool"


async def test_call_tool_handles_content_item_without_text_attribute() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    # Simulate a content item that has no 'text' attribute → getattr fallback to ""
    item = MagicMock(spec=["type"])
    item.type = "image"
    raw_result = _make_call_tool_result([item])
    session, ctx = _patched_session_and_context(call_tool_result=raw_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        result = await client.call_tool("img_tool", {})

    assert result.content == [{"type": "image", "text": ""}]


async def test_call_tool_handles_empty_content() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    raw_result = _make_call_tool_result([], is_error=False)
    session, ctx = _patched_session_and_context(call_tool_result=raw_result)

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        result = await client.call_tool("empty_tool", {})

    assert result.content == []


# ---------------------------------------------------------------------------
# call_tool — error propagation
# ---------------------------------------------------------------------------


async def test_call_tool_wraps_session_exception_in_mcp_server_error() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    session.call_tool = AsyncMock(side_effect=ValueError("bad arguments"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        with pytest.raises(MCPServerError, match="call_tool"):
            await client.call_tool("my_tool", {"x": 1})


async def test_call_tool_error_message_includes_tool_name() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    session.call_tool = AsyncMock(side_effect=RuntimeError("timeout"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        with pytest.raises(MCPServerError, match="special_tool"):
            await client.call_tool("special_tool", {})


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


async def test_disconnect_closes_session_and_context_stack() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        await client.disconnect()

    session.__aexit__.assert_awaited_once_with(None, None, None)
    ctx.__aexit__.assert_awaited_once_with(None, None, None)
    assert client._session is None
    assert client._context_stack is None


async def test_disconnect_when_not_connected_is_safe() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    # Should not raise even though _session and _context_stack are None
    await client.disconnect()
    assert client._session is None
    assert client._context_stack is None


async def test_disconnect_clears_session_even_when_session_exit_raises() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    session.__aexit__ = AsyncMock(side_effect=RuntimeError("session exit failed"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        # Should not propagate the exception
        await client.disconnect()

    assert client._session is None
    # context_stack should still be cleaned up
    ctx.__aexit__.assert_awaited_once_with(None, None, None)
    assert client._context_stack is None


async def test_disconnect_clears_context_stack_even_when_ctx_exit_raises() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    ctx.__aexit__ = AsyncMock(side_effect=RuntimeError("ctx exit failed"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        # Should not propagate the exception
        await client.disconnect()

    assert client._context_stack is None


async def test_disconnect_logs_when_config_is_set() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    config = _make_config(name="my-server")
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
        patch("jackknife.blades.mcp.client.log") as mock_log,
    ):
        await client.connect(config)
        await client.disconnect()

    # log.info should be called at least once for disconnect
    mock_log.info.assert_called()


async def test_disconnect_does_not_log_when_config_is_none() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    with patch("jackknife.blades.mcp.client.log") as mock_log:
        await client.disconnect()  # _config is None

    # Nothing to log: no server name available
    mock_log.info.assert_not_called()


# ---------------------------------------------------------------------------
# Context manager (__aenter__ / __aexit__ via BaseMCPClient)
# ---------------------------------------------------------------------------


async def test_context_manager_calls_disconnect_on_exit() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        async with client:
            await client.connect(_make_config())
            tools = await client.list_tools()

    assert tools == []
    assert client._session is None


async def test_context_manager_returns_client_instance() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    async with client as c:
        assert c is client


# ---------------------------------------------------------------------------
# health_check (inherited from BaseMCPClient; uses list_tools under the hood)
# ---------------------------------------------------------------------------


async def test_health_check_returns_true_when_list_tools_succeeds() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context(
        list_tools_result=_make_list_tools_result([{"name": "t", "description": "d"}])
    )

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        healthy = await client.health_check()

    assert healthy is True


async def test_health_check_returns_false_when_list_tools_fails() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    session, ctx = _patched_session_and_context()
    session.list_tools = AsyncMock(side_effect=RuntimeError("broken"))

    with (
        patch("jackknife.blades.mcp.client.stdio_client", return_value=ctx),
        patch("jackknife.blades.mcp.client.ClientSession", return_value=session),
    ):
        await client.connect(_make_config())
        healthy = await client.health_check()

    assert healthy is False


async def test_health_check_returns_false_when_not_connected() -> None:
    from jackknife.blades.mcp.client import MCPStdioClient

    client = MCPStdioClient()
    healthy = await client.health_check()
    assert healthy is False
