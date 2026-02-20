"""
MCP blade — server registry.

Reads [[mcp.servers]] entries from jackknife.toml and returns a list
of MCPServerConfig objects ready to pass to MCPStdioClient.connect().

jackknife.toml example:
    [[mcp.servers]]
    name = "filesystem"
    transport = "stdio"
    command = "npx"
    args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]

    [[mcp.servers]]
    name = "memory"
    transport = "stdio"
    command = "jackknife-memory-server"
    args = ["--persist-dir", "/abs/path/to/db"]
"""

from __future__ import annotations

from pathlib import Path

from jackknife.blades.mcp.models import MCPServerConfig
from jackknife.core.exceptions import MCPConfigError

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError as exc:
        raise ImportError("tomllib/tomli required for TOML parsing") from exc


class MCPRegistry:
    """Loads MCP server configs from a TOML configuration file."""

    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path("jackknife.toml")

    def load(self) -> list[MCPServerConfig]:
        """
        Parse [[mcp.servers]] from the TOML config and return MCPServerConfig list.

        Returns an empty list if the file doesn't exist or has no mcp.servers.
        Raises MCPConfigError if the TOML is malformed.
        """
        if not self._config_path.exists():
            return []
        try:
            with open(self._config_path, "rb") as f:
                data = tomllib.load(f)
        except Exception as exc:
            raise MCPConfigError(f"Failed to parse {self._config_path}: {exc}") from exc

        servers_raw = data.get("mcp", {}).get("servers", [])
        if not isinstance(servers_raw, list):
            raise MCPConfigError("mcp.servers must be a TOML array of tables")

        configs: list[MCPServerConfig] = []
        for raw in servers_raw:
            if not isinstance(raw, dict):
                raise MCPConfigError("Each mcp.servers entry must be a TOML table")
            if "name" not in raw:
                raise MCPConfigError("Each mcp.servers entry must have a 'name' field")
            try:
                configs.append(MCPServerConfig.model_validate(raw))
            except Exception as exc:
                raise MCPConfigError(
                    f"Invalid mcp.servers entry {raw.get('name', '?')!r}: {exc}"
                ) from exc

        return configs

    def get(self, name: str) -> MCPServerConfig:
        """Retrieve a single server config by name."""
        for config in self.load():
            if config.name == name:
                return config
        raise MCPConfigError(f"MCP server {name!r} not found in {self._config_path}")
