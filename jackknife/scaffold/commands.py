"""
Scaffold — `jackknife new` command implementation.

Called from cli.py after argument validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jackknife.core.logging import get_logger
from jackknife.scaffold.engine import ScaffoldEngine
from jackknife.scaffold.validators import (
    validate_output_dir,
    validate_project_name,
    validate_template,
)

log = get_logger(__name__)


def scaffold_new_project(
    project_name: str,
    template: str = "streamlit",
    output_dir: str = ".",
) -> Path:
    """
    Scaffold a new project from a template.

    Args:
        project_name: The name of the project to create.
        template: Template to use: streamlit | api
        output_dir: Directory to create the project in.

    Returns:
        The path to the created project directory.
    """
    name = validate_project_name(project_name)
    tpl = validate_template(template)
    project_path = validate_output_dir(output_dir, name)

    context: dict[str, Any] = {
        "project_name": name,
        "project_name_title": name.replace("_", " ").title(),
        "template": tpl,
    }

    engine = ScaffoldEngine()
    created = engine.render_project(tpl, project_path, context)

    log.info(
        "project_scaffolded",
        name=name,
        template=tpl,
        path=str(project_path),
        files=len(created),
    )
    return project_path
