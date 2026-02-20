"""Tests for the jackknife CLI."""

from __future__ import annotations

from typer.testing import CliRunner

from jackknife.cli import app

runner = CliRunner()


def test_app_has_expected_commands() -> None:
    """Verify the CLI app has the expected sub-commands registered."""
    group_names = [g.name for g in (app.registered_groups or [])]
    assert "memory" in group_names
    assert "add" in group_names


def test_new_command() -> None:
    result = runner.invoke(app, ["new", "my-project"])
    assert result.exit_code == 0
    assert "my-project" in result.output


def test_new_command_with_template() -> None:
    result = runner.invoke(app, ["new", "my-project", "--template", "api"])
    assert result.exit_code == 0
    assert "api" in result.output


def test_memory_store_command() -> None:
    result = runner.invoke(app, ["memory", "store", "Test memory entry"])
    assert result.exit_code == 0
    assert "Test memory entry" in result.output


def test_memory_store_with_tags() -> None:
    result = runner.invoke(
        app, ["memory", "store", "Decision: use SQLAlchemy", "--tag", "architecture"]
    )
    assert result.exit_code == 0
    assert "architecture" in result.output


def test_memory_search_command() -> None:
    result = runner.invoke(app, ["memory", "search", "SQLAlchemy"])
    assert result.exit_code == 0
    assert "SQLAlchemy" in result.output


def test_memory_sync_command() -> None:
    result = runner.invoke(app, ["memory", "sync"])
    assert result.exit_code == 0
    assert "CLAUDE.md" in result.output


def test_add_connector_command() -> None:
    result = runner.invoke(app, ["add", "connector", "sql"])
    assert result.exit_code == 0
    assert "sql" in result.output


def test_add_mcp_command() -> None:
    result = runner.invoke(app, ["add", "mcp", "brave-search"])
    assert result.exit_code == 0
    assert "brave-search" in result.output
