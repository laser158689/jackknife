"""
Memory blade — MCP server.

Exposes the jackknife memory store as an MCP server so any
MCP-capable tool (Claude Desktop, Cursor, Windsurf, custom agents)
can read and write shared project memory without Python imports.

Tools exposed:
    memory_store   Store a new memory entry
    memory_search  Semantic search over project memory
    memory_list_tags  List all tags in use

Run as a subprocess:
    python -m jackknife.blades.memory.mcp_server --persist-dir /path/to/db

Or configure in claude_desktop_config.json / jackknife.toml.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

from jackknife.blades.memory.chroma_store import ChromaMemoryStore
from jackknife.blades.memory.models import MemoryEntry
from jackknife.blades.memory.write_queue import MemoryWriteQueue
from jackknife.core.logging import configure_logging, get_logger

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError as exc:
    raise ImportError("mcp is not installed. Enable the mcp extra: poetry install -E mcp") from exc

log = get_logger(__name__)


def build_server(persist_dir: str, collection: str = "project_memory") -> Server:
    """Build and configure the MCP server with memory tools."""
    store = ChromaMemoryStore(persist_dir=persist_dir, collection_name=collection)
    queue = MemoryWriteQueue(store=store)
    server: Server = Server("jackknife-memory")

    @server.list_tools()  # type: ignore[misc, no-untyped-call, untyped-decorator]
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name="memory_store",
                description=(
                    "Store a memory entry in the project knowledge base. "
                    "Use for decisions, conventions, architecture notes, and error fixes."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "The memory content"},
                        "entry_type": {
                            "type": "string",
                            "enum": [
                                "general",
                                "decision",
                                "architecture",
                                "convention",
                                "error",
                                "fix",
                                "context",
                            ],
                            "default": "general",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "default": [],
                        },
                        "source": {
                            "type": "string",
                            "description": "Tool storing this entry (e.g. claude_code, cursor)",
                        },
                    },
                    "required": ["content"],
                },
            ),
            Tool(
                name="memory_search",
                description="Semantic search over project memory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "limit": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
            Tool(
                name="memory_list_tags",
                description="List all tags currently in use in project memory.",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()  # type: ignore[misc, untyped-decorator]
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name == "memory_store":
            entry = MemoryEntry(
                content=arguments["content"],
                entry_type=arguments.get("entry_type", "general"),
                tags=arguments.get("tags", []),
                source=arguments.get("source"),
            )
            entry_id = await queue.enqueue(entry)
            return [TextContent(type="text", text=f"Stored entry: {entry_id}")]

        if name == "memory_search":
            results = await store.search(
                query=arguments["query"],
                limit=int(arguments.get("limit", 5)),
            )
            payload = [
                {
                    "id": str(r.entry.id),
                    "content": r.entry.content,
                    "entry_type": r.entry.entry_type,
                    "tags": r.entry.tags,
                    "score": round(r.score, 4),
                }
                for r in results
            ]
            return [TextContent(type="text", text=json.dumps(payload, indent=2))]

        if name == "memory_list_tags":
            tags = await store.list_tags()
            return [TextContent(type="text", text=json.dumps(tags))]

        return [TextContent(type="text", text=f"Unknown tool: {name}")]

    return server


async def run_server(persist_dir: str, collection: str = "project_memory") -> None:
    """Start the MCP memory server over stdio."""
    configure_logging()
    store = ChromaMemoryStore(persist_dir=persist_dir, collection_name=collection)
    queue = MemoryWriteQueue(store=store)
    await queue.start()
    server = build_server(persist_dir, collection)
    log.info("mcp_memory_server_starting", persist_dir=persist_dir)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )
    await queue.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Jackknife memory MCP server")
    parser.add_argument("--persist-dir", required=True, help="ChromaDB persistence directory")
    parser.add_argument("--collection", default="project_memory", help="Collection name")
    args = parser.parse_args()
    asyncio.run(run_server(args.persist_dir, args.collection))


if __name__ == "__main__":
    main()
