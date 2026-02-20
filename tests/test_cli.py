"""Tests for the jackknife CLI."""

from __future__ import annotations

import os
from pathlib import Path

from typer.testing import CliRunner

from jackknife.cli import app

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


def test_memory_search_command(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    # Store something first so search returns results
    runner.invoke(app, ["memory", "store", "SQLAlchemy for async SQL"], env=env)
    result = runner.invoke(app, ["memory", "search", "SQLAlchemy"], env=env)
    assert result.exit_code == 0, result.output
    assert "SQLAlchemy" in result.output


def test_memory_sync_command(tmp_path: Path) -> None:
    env = {**os.environ, "MEMORY_PERSIST_DIR": str(tmp_path / "memory")}
    result = runner.invoke(
        app,
        ["memory", "sync", "--root", str(tmp_path), "--name", "TestProject"],
        env=env,
    )
    assert result.exit_code == 0, result.output
    assert "CLAUDE.md" in result.output


def test_add_connector_command() -> None:
    result = runner.invoke(app, ["add", "connector", "sql"])
    assert result.exit_code == 0
    assert "sql" in result.output


def test_add_mcp_command() -> None:
    result = runner.invoke(app, ["add", "mcp", "brave-search"])
    assert result.exit_code == 0
    assert "brave-search" in result.output
