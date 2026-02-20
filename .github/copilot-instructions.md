# Jackknife — GitHub Copilot Instructions

## Project
Python 3.12 toolkit. Poetry for all package management. FastAPI (optional), Streamlit (default UI).

## Always
- `poetry run <command>` — never `python3` or `pip`
- Create git branch before any change: `git checkout -b type/name`
- Absolute paths in config only

## Blade Pattern
`jackknife/blades/<name>/`: base.py (Protocol+ABC) → models.py (Pydantic) → factory.py → __init__.py

## Core
- `get_settings()` — pydantic-settings, lru_cached
- `get_logger(__name__)` — structlog
- `JackknifeError` — base for all exceptions
- `JackknifeBaseModel` — Pydantic base with extra="forbid"

## Style
- ruff, line-length=100, type annotations required, files ≤ 200 lines
- Conventional commits: feat: fix: docs: refactor: test: ci: chore:
