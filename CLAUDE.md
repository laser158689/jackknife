# Claude Development Guidelines for Jackknife

## What is Jackknife?

A dual-purpose foundational Python toolkit:
1. **Importable library** — "blades" (swiss army knife metaphor) any project can import
2. **Project scaffold** — `jackknife new <project>` CLI to bootstrap new projects

Future projects built with jackknife will use **parallel heterogeneous agents**
(Claude Code, Cursor, Windsurf, OpenAI Codex) sharing a common project memory.

## Python Environment — CRITICAL

**ALWAYS use Poetry. NEVER use `python3` or `pip` directly.**

```bash
poetry run python          # ✅ correct
poetry run pytest          # ✅ correct
poetry run jackknife       # ✅ correct
python3 script.py          # ❌ never
pip install package        # ❌ never
```

## Branch Strategy — MANDATORY

```bash
# ALWAYS create a branch before ANY code change
git checkout -b fix/descriptive-name
git checkout -b feature/new-blade-name
git checkout -b chore/update-description

# NEVER commit directly to main
```

## Project Structure

```
jackknife/
├── jackknife/
│   ├── core/          # Config, exceptions, logging, shared models
│   ├── blades/        # Individual capability modules
│   │   ├── llm/       # LLM provider abstraction (litellm)
│   │   ├── memory/    # Project memory (ChromaDB + MCP server)
│   │   ├── storage/   # File storage (local, S3, GCS, Azure)
│   │   ├── data/      # Data connectors (SQL, NoSQL, Graph, flat)
│   │   ├── mcp/       # MCP client + scaffold
│   │   └── agents/    # Orchestrator + worker patterns
│   ├── scaffold/      # Project template engine (Phase 7)
│   └── cli.py         # Typer CLI entry point
└── tests/             # Mirror of source structure
```

## Adding a New Blade

1. Create `jackknife/blades/<name>/` directory
2. Write `base.py` first — Protocol + ABC, no implementation yet
3. Write `models.py` — all Pydantic request/response models
4. Write `factory.py` — `create_X(settings)` function (stub with `NotImplementedError`)
5. Write `__init__.py` — export public API
6. Create `tests/blades/test_<name>/` with matching test structure
7. Add optional extra to `pyproject.toml` if new dependencies needed

## Exception Hierarchy

All exceptions inherit from `JackknifeError`:

```
JackknifeError
├── ConfigurationError    # Missing/invalid config
├── ValidationError       # Input validation failed
├── LLMError → LLMConnectionError, LLMRateLimitError, LLMResponseError
├── StorageError → StorageConnectionError, StorageNotFoundError
├── MemoryError → MemoryWriteError, MemorySearchError
├── DataConnectorError → SQLConnectorError, NoSQLConnectorError, GraphConnectorError
├── MCPError → MCPServerError, MCPConfigError
├── AgentError → OrchestratorError, WorkerError
└── ScaffoldError
```

## Configuration System

- `jackknife.toml` — non-secret project config (committed to VCS)
- `.env` — secrets only (NEVER committed, NEVER relative paths)
- `jackknife/core/config.py` — `get_settings()` loads both via pydantic-settings
- **ALL paths in config MUST be absolute**

```python
from jackknife.core.config import get_settings
settings = get_settings()
# settings is cached — safe to call anywhere
```

## Logging

```python
from jackknife.core.logging import get_logger
log = get_logger(__name__)
log.info("operation_complete", key="value", count=42)
log.error("operation_failed", error=str(exc))
```

## Code Quality Standards

- Files must NOT exceed 200 lines
- Run before committing:

```bash
poetry run ruff check . --fix    # Lint + auto-fix
poetry run ruff format .          # Format
poetry run mypy jackknife/        # Type check
poetry run pytest                 # Tests + coverage
poetry run pre-commit run --all-files  # All hooks
```

## Conventional Commits — REQUIRED

```
feat: add neo4j graph connector
fix: resolve memory write queue deadlock
docs: update memory blade README
refactor: extract base connector to ABC
test: add integration tests for litellm adapter
ci: add codecov step to test workflow
chore: update ruff to 0.8.4
```

## Build Phases

| Phase | Blade | Status |
|-------|-------|--------|
| 1 | Foundation (core, interfaces, CI/CD) | ✅ Complete |
| 2 | Memory blade (ChromaDB, MCP server, dev file sync) | Pending |
| 3 | LLM blade (litellm adapter) | Pending |
| 4 | Data blade (SQL, NoSQL, Graph, flat files) | Pending |
| 5 | Storage blade (local, S3, GCS, Azure) | Pending |
| 6 | Agents blade (orchestrator, workers, task graph) | Pending |
| 7 | Scaffold CLI (`jackknife new`) | Pending |

## Key Commands

```bash
# Setup
poetry install --all-extras
poetry run pre-commit install

# Development
poetry run ruff check . --fix
poetry run ruff format .
poetry run mypy jackknife/
poetry run pytest
poetry run jackknife --help

# Add a dependency (blade-specific)
poetry add <package> --optional
# Then add to the relevant extra in pyproject.toml

# CI/CD
git tag v0.1.1 && git push origin v0.1.1   # Triggers PyPI publish
poetry run cz bump                           # Auto-bump version from commits
```
