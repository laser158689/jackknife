"""
Jackknife CLI — entry point.

Commands:
  jackknife new <project-name>           Scaffold a new project from template
  jackknife memory store <text>          Store a memory entry
  jackknife memory search <query>        Semantic search over project memory
  jackknife memory sync                  Regenerate all dev tool context files
  jackknife add connector <type>         Add a data connector to current project
  jackknife add mcp <server-name>        Add an MCP server connection

Usage:
    poetry run jackknife --help
"""

from __future__ import annotations

import typer

from jackknife.core.logging import configure_logging, get_logger

app = typer.Typer(
    name="jackknife",
    help="A foundational toolkit for building AI-powered Python projects.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

memory_app = typer.Typer(help="Project memory operations.")
add_app = typer.Typer(help="Add capabilities to an existing project.")

app.add_typer(memory_app, name="memory")
app.add_typer(add_app, name="add")

log = get_logger(__name__)


def _startup() -> None:
    """Configure logging at CLI startup."""
    configure_logging()


# ── Top-level commands ────────────────────────────────────────────────────────


@app.command()
def new(
    project_name: str = typer.Argument(..., help="Name of the new project"),
    template: str = typer.Option(
        "streamlit", "--template", "-t", help="Project template: streamlit | api"
    ),
    output_dir: str = typer.Option(
        ".", "--output", "-o", help="Directory to create the project in"
    ),
) -> None:
    """Scaffold a new project from a template."""
    _startup()
    typer.echo(f"Creating project '{project_name}' with template '{template}' in '{output_dir}'")
    typer.echo("Scaffold CLI coming in Phase 7.")
    raise typer.Exit(0)


# ── Memory commands ───────────────────────────────────────────────────────────


@memory_app.command("store")
def memory_store(
    text: str = typer.Argument(..., help="Content to store in project memory"),
    tags: list[str] = typer.Option([], "--tag", "-t", help="Tags to attach (repeatable)"),  # noqa: B008
    entry_type: str = typer.Option(
        "general",
        "--type",
        help="Entry type: general | decision | architecture | convention | error | fix",
    ),
) -> None:
    """Store a memory entry in the project knowledge base."""
    _startup()
    tag_str = ", ".join(tags) if tags else "none"
    typer.echo(f"Storing [{entry_type}]: {text[:80]}...")
    typer.echo(f"Tags: {tag_str}")
    typer.echo("Memory blade coming in Phase 2.")
    raise typer.Exit(0)


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(..., help="Semantic search query"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of results to return"),
) -> None:
    """Search project memory using semantic similarity."""
    _startup()
    typer.echo(f"Searching memory for: {query!r} (top {limit})")
    typer.echo("Memory blade coming in Phase 2.")
    raise typer.Exit(0)


@memory_app.command("sync")
def memory_sync() -> None:
    """Regenerate all dev tool context files from project memory."""
    _startup()
    files = [
        "CLAUDE.md",
        ".cursorrules",
        ".windsurfrules",
        "AGENTS.md",
        ".github/copilot-instructions.md",
        ".augment/guidelines.md",
    ]
    typer.echo("Syncing dev tool context files:")
    for f in files:
        typer.echo(f"  → {f}")
    typer.echo("Memory blade coming in Phase 2.")
    raise typer.Exit(0)


# ── Add commands ──────────────────────────────────────────────────────────────


@add_app.command("connector")
def add_connector(
    connector_type: str = typer.Argument(
        ..., help="Connector type: sql | mongodb | redis | neo4j | csv | excel | parquet"
    ),
) -> None:
    """Add a data connector to the current project."""
    _startup()
    typer.echo(f"Adding {connector_type!r} connector...")
    typer.echo("Data blade coming in Phase 4.")
    raise typer.Exit(0)


@add_app.command("mcp")
def add_mcp(
    server_name: str = typer.Argument(..., help="MCP server name or package"),
) -> None:
    """Add an MCP server connection to jackknife.toml."""
    _startup()
    typer.echo(f"Adding MCP server: {server_name!r}")
    typer.echo("MCP client coming in Phase 2.")
    raise typer.Exit(0)


if __name__ == "__main__":
    app()
