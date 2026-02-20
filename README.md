# jackknife

A dual-purpose foundational Python toolkit.

1. **Importable blades** — modular capabilities (LLM, memory, storage, data, MCP, agents)
2. **Project scaffold** — `jackknife new <project>` to bootstrap new projects

## Quick Start

```bash
poetry install
poetry run jackknife --help
```

## Blades

| Blade | Description | Status |
|-------|-------------|--------|
| `llm` | LLM-agnostic provider abstraction (litellm) | Phase 3 |
| `memory` | Project memory with semantic search (ChromaDB) | Phase 2 |
| `storage` | File storage (local, S3, GCS, Azure) | Phase 5 |
| `data` | Data connectors (SQL, NoSQL, Graph, flat files) | Phase 4 |
| `mcp` | MCP client + server scaffold | Phase 2 |
| `agents` | Orchestrator + worker agent patterns | Phase 6 |

## Development

```bash
poetry install --all-extras
poetry run pre-commit install
poetry run pytest
```
