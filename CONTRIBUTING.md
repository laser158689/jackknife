# Contributing

## Setup

```bash
git clone https://github.com/laser158689/jackknife.git
cd jackknife
poetry install --all-extras
poetry run pre-commit install
```

## Workflow

1. Create a branch: `git checkout -b fix/description` or `feat/description`
2. Make changes
3. Run the quality gate before pushing:

```bash
poetry run ruff check .
poetry run ruff format .
poetry run mypy jackknife/
poetry run pytest
```

4. Commit using [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` — new feature
   - `fix:` — bug fix
   - `chore:` — maintenance
   - `docs:` — documentation
   - `refactor:` — code restructure without behavior change
   - `test:` — test additions or changes
   - `ci:` — CI/CD changes

5. Push and open a PR — CI must pass before merge.

## Adding a blade

Each blade lives under `jackknife/blades/<name>/` and follows this structure:

```
blades/<name>/
├── __init__.py    # re-exports
├── base.py        # Protocol + ABC
├── models.py      # Pydantic request/response types
├── factory.py     # create_X(settings) → BaseX
└── <impl>.py      # concrete implementation(s)
```

Add the blade as an optional extra in `pyproject.toml` so the base install stays lean.

## Running tests

```bash
poetry run pytest                        # all tests
poetry run pytest tests/blades/test_llm  # specific blade
poetry run pytest -k "test_store"        # by name pattern
```

Coverage must stay at or above 80%.
