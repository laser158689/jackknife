# jackknife

[![CI](https://github.com/laser158689/jackknife/actions/workflows/test.yml/badge.svg)](https://github.com/laser158689/jackknife/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A dual-purpose foundational Python toolkit for AI-powered application development.

1. **Importable blades** — modular, protocol-driven capabilities you drop into any project
2. **Project scaffold** — `jackknife new <project>` bootstraps a full project with all dev-tool context files

```
pip install jackknife                          # base only
pip install "jackknife[llm,memory,agents]"    # pick your blades
pip install "jackknife[all]"                  # everything
```

---

## Blades

Each blade is an optional extra. Install only what you need.

| Blade | Extra | What it gives you |
|---|---|---|
| `llm` | `llm` | LLM-agnostic provider via [litellm](https://github.com/BerriAI/litellm) — 100+ models, one interface |
| `memory` | `memory` | Semantic project memory via ChromaDB + sentence-transformers; MCP server included |
| `storage` | `storage-s3` / `storage-gcs` / `storage-azure` | File storage abstraction for local, S3, GCS, and Azure Blob |
| `data` | `data-sql` / `data-nosql` / `data-graph` / `data-flat` | Async connectors for PostgreSQL, MySQL, SQLite, MongoDB, Redis, Neo4j, pandas |
| `mcp` | `mcp` | TOML-driven MCP client; consume any MCP server from `jackknife.toml` |
| `agents` | `agents` | Task-graph orchestrator (networkx DAG) + stateless worker pattern |
| `api` | `api` | FastAPI + uvicorn |
| `frontend` | `frontend` | Streamlit |

### Pattern

Every blade follows the same structure:

```
blades/<name>/
├── base.py        # Protocol (duck-typing) + ABC (enforced inheritance)
├── models.py      # Pydantic request/response types
├── factory.py     # create_X(settings) → BaseX
└── <impl>.py      # Concrete implementation(s)
```

---

## Quick Start

### Install

```bash
# Development (all extras)
poetry install --all-extras
poetry run pre-commit install

# Production (pick blades)
pip install "jackknife[llm,memory,agents]"
```

### Configure

Copy `.env.example` to `.env` and fill in secrets. Non-secret config goes in `jackknife.toml`:

```toml
[llm]
provider = "openai"
model    = "gpt-4o-mini"

[memory]
persist_dir = "/absolute/path/to/memory_db"

[storage]
backend   = "local"
base_path = "/absolute/path/to/files"
```

### CLI

```bash
# Scaffold a new project
jackknife new my-app --template streamlit
jackknife new my-api --template api

# Project memory
jackknife memory store "Use SQLAlchemy async for all SQL" --tag architecture
jackknife memory search "SQL database"
jackknife memory sync          # regenerates CLAUDE.md, .cursorrules, AGENTS.md, etc.

# Add connectors / MCP servers to an existing project
jackknife add connector
jackknife add mcp
```

---

## Use as a Library

```python
from jackknife.blades.llm.factory import create_llm
from jackknife.blades.memory.factory import create_memory_store
from jackknife.blades.agents.factory import create_orchestrator
from jackknife.core.config import get_settings

settings = get_settings()

# LLM
llm = create_llm(settings)
response = await llm.complete(LLMRequest(messages=[{"role": "user", "content": "hello"}]))

# Memory
store = create_memory_store(settings)
await store.store(MemoryEntry(content="Use async SQLAlchemy", tags=["architecture"]))
results = await store.search("database pattern")

# Agents
orchestrator = create_orchestrator(max_parallel=4)
```

---

## Memory Blade — Multi-Agent Context Sync

The memory blade solves a real problem: when multiple AI coding tools (Claude, Cursor, Windsurf, Codex) work on the same project, each starts with a blank slate.

`jackknife memory sync` reads entries tagged `architecture`, `decision`, or `convention` from the vector store and renders them into every dev-tool context file:

| File | Tool |
|---|---|
| `CLAUDE.md` | Claude Code |
| `.cursorrules` | Cursor |
| `.windsurfrules` | Windsurf |
| `AGENTS.md` | OpenAI Codex / Agents |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.augment/guidelines.md` | Augment Code |

The memory store is also exposed as an MCP server (`blades/memory/mcp_server.py`), so any MCP-capable tool can read and write shared project memory without Python imports.

---

## Development

```bash
# Quality gates (same as CI)
poetry run ruff check .
poetry run ruff format --check .
poetry run mypy jackknife/
poetry run pytest

# All at once via pre-commit
poetry run pre-commit run --all-files
```

### CI/CD

| Workflow | Trigger | Steps |
|---|---|---|
| `test.yml` | Push / PR to main | ruff → mypy → pytest (coverage ≥ 80%) |
| `publish.yml` | `v*` tag | poetry build → PyPI Trusted Publishing (OIDC) |

---

## Stack

| Concern | Choice |
|---|---|
| Package management | Poetry |
| Config | pydantic-settings (`.env` + `jackknife.toml`) |
| LLM abstraction | litellm |
| Vector store | ChromaDB |
| Embeddings | sentence-transformers |
| MCP | Anthropic `mcp` SDK |
| CLI | Typer |
| Logging | structlog (JSON in prod, colored in dev) |
| Lint / format | ruff |
| Type checking | mypy (strict) |
| Testing | pytest + pytest-asyncio (`asyncio_mode = "auto"`) |

---

## License

MIT
