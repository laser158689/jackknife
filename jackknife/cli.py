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

import asyncio
from pathlib import Path

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
    from jackknife.core.exceptions import ScaffoldError
    from jackknife.scaffold.commands import scaffold_new_project

    try:
        project_path = scaffold_new_project(
            project_name=project_name,
            template=template,
            output_dir=output_dir,
        )
        typer.echo(f"Created project '{project_name}' at {project_path}")
        typer.echo(f"  cd {project_path.name}")
        typer.echo("  poetry install")
        typer.echo("  cp .env.example .env")
    except ScaffoldError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from exc


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
    from jackknife.core.config import get_settings
    from jackknife.core.exceptions import ConfigurationError

    settings = get_settings()
    if not settings.memory.persist_dir:
        typer.echo("Error: MEMORY_PERSIST_DIR is not set. Add it to your .env file.", err=True)
        raise typer.Exit(1)

    async def _store() -> str:
        from jackknife.blades.memory.chroma_store import ChromaMemoryStore
        from jackknife.blades.memory.models import MemoryEntry
        from jackknife.blades.memory.write_queue import MemoryWriteQueue

        store = ChromaMemoryStore(settings.memory.persist_dir, settings.memory.collection)
        queue = MemoryWriteQueue(store)
        await queue.start()
        entry = MemoryEntry(
            content=text,
            tags=tags,
            entry_type=entry_type,  # type: ignore[arg-type]
            source="cli",
        )
        entry_id = await queue.enqueue(entry)
        await queue.stop()
        return entry_id

    try:
        entry_id = asyncio.run(_store())
        tag_str = ", ".join(tags) if tags else "none"
        typer.echo(f"Stored [{entry_type}]: {text[:80]}")
        typer.echo(f"  ID: {entry_id}")
        typer.echo(f"  Tags: {tag_str}")
    except ConfigurationError as exc:
        typer.echo(f"Configuration error: {exc}", err=True)
        raise typer.Exit(1) from exc
    except Exception as exc:
        typer.echo(f"Error storing memory: {exc}", err=True)
        raise typer.Exit(1) from exc


@memory_app.command("search")
def memory_search(
    query: str = typer.Argument(..., help="Semantic search query"),
    limit: int = typer.Option(5, "--limit", "-n", help="Number of results to return"),
) -> None:
    """Search project memory using semantic similarity."""
    _startup()
    from jackknife.core.config import get_settings

    settings = get_settings()
    if not settings.memory.persist_dir:
        typer.echo("Error: MEMORY_PERSIST_DIR is not set. Add it to your .env file.", err=True)
        raise typer.Exit(1)

    async def _search() -> None:
        from jackknife.blades.memory.chroma_store import ChromaMemoryStore

        store = ChromaMemoryStore(settings.memory.persist_dir, settings.memory.collection)
        results = await store.search(query, limit=limit)
        if not results:
            typer.echo("No results found.")
            return
        typer.echo(f"Top {len(results)} results for {query!r}:\n")
        for i, r in enumerate(results, 1):
            tags = ", ".join(r.entry.tags) if r.entry.tags else "—"
            typer.echo(f"{i}. [{r.entry.entry_type}] score={r.score:.3f}")
            typer.echo(f"   {r.entry.content[:120]}")
            typer.echo(f"   tags: {tags}\n")

    try:
        asyncio.run(_search())
    except Exception as exc:
        typer.echo(f"Error searching memory: {exc}", err=True)
        raise typer.Exit(1) from exc


@memory_app.command("sync")
def memory_sync(
    project_root: str = typer.Option(".", "--root", "-r", help="Project root directory"),
    project_name: str = typer.Option("Project", "--name", "-n", help="Project name for headers"),
) -> None:
    """Regenerate all dev tool context files from project memory."""
    _startup()
    from jackknife.core.config import get_settings

    settings = get_settings()
    if not settings.memory.persist_dir:
        typer.echo("Error: MEMORY_PERSIST_DIR is not set. Add it to your .env file.", err=True)
        raise typer.Exit(1)

    async def _sync() -> list[str]:
        from jackknife.blades.memory.chroma_store import ChromaMemoryStore
        from jackknife.blades.memory.context_files import sync_context_files
        from jackknife.blades.memory.retriever import MemoryRetriever

        store = ChromaMemoryStore(settings.memory.persist_dir, settings.memory.collection)
        retriever = MemoryRetriever(store)
        return await sync_context_files(
            retriever=retriever,
            project_root=Path(project_root),
            project_name=project_name,
        )

    try:
        written = asyncio.run(_sync())
        typer.echo("Synced dev tool context files:")
        for f in written:
            typer.echo(f"  → {f}")
    except Exception as exc:
        typer.echo(f"Error syncing context files: {exc}", err=True)
        raise typer.Exit(1) from exc


# ── Add commands ──────────────────────────────────────────────────────────────


@add_app.command("connector")
def add_connector(
    connector_type: str = typer.Argument(
        ..., help="Connector type: sql | mongodb | redis | neo4j | csv | excel | parquet"
    ),
) -> None:
    """Add a data connector to the current project."""
    _startup()
    valid = {"sql", "mongodb", "redis", "neo4j", "csv", "excel", "parquet"}
    if connector_type not in valid:
        typer.echo(
            f"Error: Unknown connector type {connector_type!r}. Valid: {sorted(valid)}", err=True
        )
        raise typer.Exit(1)
    typer.echo(f"Adding {connector_type!r} connector...")
    typer.echo("Run: poetry install -E data-sql  (or the appropriate extra)")
    typer.echo(f"Then import: from jackknife.blades.data.{connector_type} import ...")


@add_app.command("mcp")
def add_mcp(
    server_name: str = typer.Argument(..., help="MCP server name or package"),
) -> None:
    """Add an MCP server connection to jackknife.toml."""
    _startup()
    typer.echo(f"To add MCP server {server_name!r}, add this to jackknife.toml:\n")
    typer.echo("[[mcp.servers]]")
    typer.echo(f'name = "{server_name}"')
    typer.echo('transport = "stdio"')
    typer.echo('command = "npx"')
    typer.echo(f'args = ["-y", "@modelcontextprotocol/server-{server_name}"]')


if __name__ == "__main__":
    app()
