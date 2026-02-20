"""Scaffold — project name and output path validation."""

from __future__ import annotations

import re
from pathlib import Path

from jackknife.core.exceptions import ScaffoldError

# Python package names: lowercase letters, digits, underscores/hyphens, starts with letter
_VALID_NAME = re.compile(r"^[a-z][a-z0-9_-]*$")
_RESERVED = {"jackknife", "test", "tests", "setup", "dist", "build", "venv", ".venv"}


def validate_project_name(name: str) -> str:
    """
    Validate a project name for use as a Python package.

    Returns the validated name (normalized to lowercase with underscores).
    Raises ScaffoldError with a clear message if invalid.
    """
    normalized = name.lower().replace("-", "_")
    if not normalized:
        raise ScaffoldError("Project name cannot be empty")
    if not _VALID_NAME.match(normalized):
        raise ScaffoldError(
            f"Invalid project name {name!r}. "
            "Use lowercase letters, digits, underscores, or hyphens. "
            "Must start with a letter."
        )
    if normalized in _RESERVED:
        raise ScaffoldError(f"Project name {name!r} is reserved. Choose a different name.")
    return normalized


def validate_output_dir(output_dir: str, project_name: str) -> Path:
    """
    Validate the output directory and ensure the target project folder doesn't exist.

    Returns the full project path (output_dir / project_name).
    Raises ScaffoldError if the directory already exists.
    """
    base = Path(output_dir).resolve()
    if not base.exists():
        raise ScaffoldError(
            f"Output directory does not exist: {output_dir!r}. "
            "Create it first or choose a different path."
        )
    if not base.is_dir():
        raise ScaffoldError(f"Output path is not a directory: {output_dir!r}")

    project_path = base / project_name
    if project_path.exists():
        raise ScaffoldError(
            f"Project directory already exists: {project_path}. "
            "Choose a different name or output directory."
        )
    return project_path


def validate_template(template: str) -> str:
    """Validate the template name. Returns normalized template name."""
    valid = {"streamlit", "api"}
    if template not in valid:
        raise ScaffoldError(f"Unknown template {template!r}. Available templates: {sorted(valid)}")
    return template
