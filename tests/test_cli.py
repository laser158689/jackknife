"""Tests for the jackknife CLI."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from jackknife.cli import app
from jackknife.core.config import get_settings

runner = CliRunner()


def test_app_has_expected_commands() -> None:
    """Verify the CLI app has the expected sub-commands registered."""
    group_names = [g.name for g in (app.registered_groups or [])]
    assert "memory" in group_names
    assert "add" in group_names


def test_new_command(tmp_path: Path) -> None:
    result = runner.invoke(app, ["new", "my-project", "--output", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "my-project" in result.output


def test_new_command_with_template(tmp_path: Path) -> None:
    result = runner.invoke(app, ["new", "my-api", "--template", "api", "--output", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "api" in result.output


# ── Lines 74-76: new command ScaffoldError ────────────────────────────────────


def test_new_command_scaffold_error(tmp_path: Path) -> None:
    """Covers lines 74-76: ScaffoldError is caught and Exit(1) raised."""
    from jackknife.core.exceptions import ScaffoldError

    with patch(
        "jackknife.scaffold.commands.scaffold_new_project",
        side_effect=ScaffoldError("bad template"),
    ):
        result = runner.invoke(app, ["new", "broken-proj", "--output", str(tmp_path)])
    assert result.exit_code == 1
    assert "Error:" in result.output


def test_memory_store_command(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    result = runner.invoke(app, ["memory", "store", "Test memory entry"], env=env)
    assert result.exit_code == 0, result.output
    assert "Test memory entry" in result.output


def test_memory_store_with_tags(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    result = runner.invoke(
        app,
        ["memory", "store", "Decision: use SQLAlchemy", "--tag", "architecture"],
        env=env,
    )
    assert result.exit_code == 0, result.output
    assert "architecture" in result.output


# ── Lines 99-100: memory store missing persist_dir ───────────────────────────


def test_memory_store_missing_persist_dir() -> None:
    """Covers lines 99-100: exits with error when MEMORY_PERSIST_DIR is not set."""
    get_settings.cache_clear()
    env = {k: v for k, v in os.environ.items() if k != "MEMORY_PERSIST_DIR"}
    env.pop("MEMORY_PERSIST_DIR", None)
    result = runner.invoke(app, ["memory", "store", "some text"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "MEMORY_PERSIST_DIR" in result.output


# ── Lines 126-128: memory store ConfigurationError ───────────────────────────


def test_memory_store_configuration_error(tmp_path: Path) -> None:
    """Covers lines 126-128: ConfigurationError is caught and Exit(1) raised."""
    from jackknife.core.exceptions import ConfigurationError

    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}

    with patch(
        "jackknife.blades.memory.chroma_store.ChromaMemoryStore",
        side_effect=ConfigurationError("bad config"),
    ):
        result = runner.invoke(app, ["memory", "store", "some text"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "Configuration error:" in result.output


# ── Lines 129-131: memory store generic Exception ────────────────────────────


def test_memory_store_generic_exception(tmp_path: Path) -> None:
    """Covers lines 129-131: generic Exception is caught and Exit(1) raised."""
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}

    with patch(
        "jackknife.blades.memory.chroma_store.ChromaMemoryStore",
        side_effect=RuntimeError("unexpected"),
    ):
        result = runner.invoke(app, ["memory", "store", "some text"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "Error storing memory:" in result.output


def test_memory_search_command(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    # Store something first so search returns results
    runner.invoke(app, ["memory", "store", "SQLAlchemy for async SQL"], env=env)
    result = runner.invoke(app, ["memory", "search", "SQLAlchemy"], env=env)
    assert result.exit_code == 0, result.output
    assert "SQLAlchemy" in result.output


# ── Lines 145-146: memory search missing persist_dir ─────────────────────────


def test_memory_search_missing_persist_dir() -> None:
    """Covers lines 145-146: exits with error when MEMORY_PERSIST_DIR is not set."""
    get_settings.cache_clear()
    env = {k: v for k, v in os.environ.items() if k != "MEMORY_PERSIST_DIR"}
    env.pop("MEMORY_PERSIST_DIR", None)
    result = runner.invoke(app, ["memory", "search", "something"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "MEMORY_PERSIST_DIR" in result.output


# ── Lines 154-155: memory search no results ───────────────────────────────────


def test_memory_search_no_results(tmp_path: Path) -> None:
    """Covers lines 154-155: 'No results found.' when store returns empty list."""
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}

    mock_store = MagicMock()
    mock_store.search = AsyncMock(return_value=[])

    with patch("jackknife.blades.memory.chroma_store.ChromaMemoryStore", return_value=mock_store):
        result = runner.invoke(app, ["memory", "search", "nothing-matches"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 0
    assert "No results found." in result.output


# ── Lines 165-167: memory search generic Exception ───────────────────────────


def test_memory_search_generic_exception(tmp_path: Path) -> None:
    """Covers lines 165-167: generic Exception is caught and Exit(1) raised."""
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}

    with patch(
        "jackknife.blades.memory.chroma_store.ChromaMemoryStore",
        side_effect=RuntimeError("search failed"),
    ):
        result = runner.invoke(app, ["memory", "search", "anything"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "Error searching memory:" in result.output


def test_memory_sync_command(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    result = runner.invoke(
        app,
        ["memory", "sync", "--root", str(tmp_path), "--name", "TestProject"],
        env=env,
    )
    assert result.exit_code == 0, result.output
    assert "CLAUDE.md" in result.output


# ── Lines 181-182: memory sync missing persist_dir ───────────────────────────


def test_memory_sync_missing_persist_dir() -> None:
    """Covers lines 181-182: exits with error when MEMORY_PERSIST_DIR is not set."""
    get_settings.cache_clear()
    env = {k: v for k, v in os.environ.items() if k != "MEMORY_PERSIST_DIR"}
    env.pop("MEMORY_PERSIST_DIR", None)
    result = runner.invoke(app, ["memory", "sync"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "MEMORY_PERSIST_DIR" in result.output


# ── Lines 202-204: memory sync generic Exception ──────────────────────────────


def test_memory_sync_generic_exception(tmp_path: Path) -> None:
    """Covers lines 202-204: generic Exception is caught and Exit(1) raised."""
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}

    with patch(
        "jackknife.blades.memory.chroma_store.ChromaMemoryStore",
        side_effect=RuntimeError("sync failed"),
    ):
        result = runner.invoke(app, ["memory", "sync"], env=env)
    get_settings.cache_clear()
    assert result.exit_code == 1
    assert "Error syncing context files:" in result.output


def test_add_connector_command() -> None:
    result = runner.invoke(app, ["add", "connector", "sql"])
    assert result.exit_code == 0
    assert "sql" in result.output


# ── Lines 220-223: add connector unknown type ─────────────────────────────────


def test_add_connector_invalid_type() -> None:
    """Covers lines 220-223: unknown connector type prints error and exits with 1."""
    result = runner.invoke(app, ["add", "connector", "invalid-type"])
    assert result.exit_code == 1
    assert "Error: Unknown connector type" in result.output
    assert "invalid-type" in result.output


def test_add_mcp_command() -> None:
    result = runner.invoke(app, ["add", "mcp", "brave-search"])
    assert result.exit_code == 0
    assert "brave-search" in result.output


# ── Line 244: __main__ entry point ────────────────────────────────────────────


def test_main_entry_point() -> None:
    """Covers line 244: app() is invoked when the module runs as __main__."""
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-m", "jackknife.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "jackknife" in result.stdout.lower()
