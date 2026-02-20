# Jackknife — Agent Guidelines

## Setup

```bash
cd /Users/brianraney/Documents/GitHub/jackknife
poetry install --all-extras
poetry run pre-commit install
poetry run python -c "import jackknife; print(jackknife.__version__)"
```

## MANDATORY: Python Command Rules
- ALWAYS: `poetry run python`, `poetry run pytest`
- NEVER: `python3`, `pip install`

## MANDATORY: Branch Workflow
```bash
git checkout -b <type>/<description>
# Make focused changes (one logical change per commit)
git add <specific-files>
git commit -m "type: description"
# Do NOT push unless instructed
```

## Architecture

### Blade Pattern
Every capability is a "blade" in `jackknife/blades/<name>/`:
```
base.py     → Protocol + ABC (structural + enforced typing)
models.py   → Pydantic I/O models (extra="forbid")
factory.py  → create_X(settings) → BaseX
__init__.py → public exports
```

### Core Utilities
```python
from jackknife.core.config import get_settings      # lru_cached Settings
from jackknife.core.logging import get_logger       # structlog
from jackknife.core.exceptions import JackknifeError
from jackknife.core.models import JackknifeBaseModel
```

### Exception Hierarchy
```
JackknifeError → ConfigurationError, ValidationError,
  LLMError, StorageError, MemoryError,
  DataConnectorError, MCPError, AgentError, ScaffoldError
```

## Quality Gates — Run Before Every Commit
```bash
poetry run ruff check . --fix
poetry run ruff format .
poetry run mypy jackknife/
poetry run pytest
```

## Testing
```bash
poetry run pytest                              # All tests
poetry run pytest tests/blades/test_memory/   # Single blade
poetry run pytest -v --tb=short               # Verbose
poetry run pytest --no-cov                    # Skip coverage (faster)
```

## Configuration
- `jackknife.toml` — non-secret project config (committed)
- `.env` — secrets only (never committed, never relative paths)
- ALL paths must be absolute

## Conventional Commits
Format: `type(optional-scope): description`
Types: `feat` `fix` `docs` `refactor` `test` `ci` `chore`
