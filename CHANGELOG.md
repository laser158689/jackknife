# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.1.0] - 2026-02-22

### Added
- **Phase 1 — Foundation**: `core` module with `pydantic-settings` config, structured logging via `structlog`, exception hierarchy, shared Pydantic base models
- **Phase 2 — Memory blade**: ChromaDB-backed semantic memory store, async write queue, MCP server, context file sync (`CLAUDE.md`, `.cursorrules`, `.windsurfrules`, `AGENTS.md`, `.github/copilot-instructions.md`, `.augment/guidelines.md`)
- **Phase 3 — LLM blade**: `litellm`-backed provider abstraction with streaming support
- **Phase 4 — Data blade**: Async connectors for PostgreSQL/MySQL/SQLite (SQLAlchemy), MongoDB (motor), Redis, Neo4j, and flat files (pandas/openpyxl/pyarrow)
- **Phase 5 — Storage blade**: File storage abstraction for local filesystem, AWS S3, Google Cloud Storage, and Azure Blob
- **Phase 6 — Agents blade**: `networkx` DAG-based task graph orchestrator and stateless worker pattern
- **Phase 7 — Scaffold**: `jackknife new` CLI command with Streamlit and FastAPI project templates; auto-generates all dev-tool context files
- Protocol + ABC pattern on all blade interfaces for duck-typing and enforced inheritance
- `create_X(settings)` factory functions on every blade
- GitHub Actions CI (`test.yml`) and PyPI publish workflow (`publish.yml`)
- Pre-commit hooks: ruff, mypy, conventional commits, branch protection
- Dependabot configuration for weekly dependency and Actions updates
- README with badges, blade overview, usage examples
- Branch protection rules on `main` (CI required, no force push)
- PR template and issue templates (bug report, feature request, question)
- MIT license

### Dependencies updated (post-launch)
- `aiofiles` ^24.1 → ^25.1
- `aiomysql` ^0.2 → ^0.3
- `asyncpg` ^0.30 → ^0.31
- `aiosqlite` ^0.20 → ^0.22
- `chromadb` ^0.6 → ^1.5
- `google-cloud-storage` ^2.18 → ^3.9
- `neo4j` ^5.26 → ^6.1
- `pytest-cov` ^6.0 → ^7.0
- `redis` ^5.0 → ^7.2
- `ruff` ^0.8 → ^0.15
- `sentence-transformers` ^3.1 → ^5.2
- `structlog` ^24.4 → ^25.5
- `typer` ^0.13 → ^0.23
- `types-aiofiles` ^24.1 → ^25.1
- `uvicorn` ^0.32 → ^0.41
- `actions/cache` 4 → 5
- `actions/checkout` 4 → 6
- `actions/setup-python` 5 → 6

[Unreleased]: https://github.com/laser158689/jackknife/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/laser158689/jackknife/releases/tag/v0.1.0
