"""Tests for MCPRegistry."""

from __future__ import annotations

import pytest

from jackknife.blades.mcp.registry import MCPRegistry
from jackknife.core.exceptions import MCPConfigError


def test_load_returns_empty_for_missing_file(tmp_path):
    registry = MCPRegistry(config_path=tmp_path / "nonexistent.toml")
    assert registry.load() == []


def test_load_returns_empty_for_no_mcp_section(tmp_path):
    toml = tmp_path / "jackknife.toml"
    toml.write_text("[project]\nname = 'test'\n")
    registry = MCPRegistry(config_path=toml)
    assert registry.load() == []


def test_load_parses_servers(tmp_path):
    toml = tmp_path / "jackknife.toml"
    toml.write_text("""
[[mcp.servers]]
name = "filesystem"
transport = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem"]
""")
    registry = MCPRegistry(config_path=toml)
    configs = registry.load()
    assert len(configs) == 1
    assert configs[0].name == "filesystem"
    assert configs[0].command == "npx"
    assert configs[0].transport == "stdio"


def test_get_finds_server_by_name(tmp_path):
    toml = tmp_path / "jackknife.toml"
    toml.write_text("""
[[mcp.servers]]
name = "memory"
command = "jackknife-memory-server"
""")
    registry = MCPRegistry(config_path=toml)
    config = registry.get("memory")
    assert config.name == "memory"


def test_get_raises_for_unknown_server(tmp_path):
    toml = tmp_path / "jackknife.toml"
    toml.write_text("")
    registry = MCPRegistry(config_path=toml)
    with pytest.raises(MCPConfigError, match="not found"):
        registry.get("unknown")


def test_load_raises_for_invalid_toml(tmp_path):
    toml = tmp_path / "bad.toml"
    toml.write_text("this is not valid toml [[[")
    registry = MCPRegistry(config_path=toml)
    with pytest.raises(MCPConfigError):
        registry.load()
