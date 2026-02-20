"""
Scaffold — Jinja2 template rendering engine.

Renders project templates from the `templates/` directory into a target path.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from jackknife.core.exceptions import ScaffoldError
from jackknife.core.logging import get_logger

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError as exc:
    raise ImportError("jinja2 is not installed. Run: poetry add jinja2") from exc

log = get_logger(__name__)

# Templates live alongside the package, two levels up from this file
_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"


class ScaffoldEngine:
    """
    Renders Jinja2 templates from the `templates/<template_name>/` directory
    into a target project directory.
    """

    def __init__(self, templates_dir: Path | None = None) -> None:
        self._templates_dir = templates_dir or _TEMPLATES_DIR
        if not self._templates_dir.exists():
            raise ScaffoldError(
                f"Templates directory not found: {self._templates_dir}. "
                "Ensure jackknife is installed correctly."
            )

    def render_project(
        self,
        template_name: str,
        project_path: Path,
        context: dict[str, Any],
    ) -> list[Path]:
        """
        Render all template files into project_path.

        Files ending in `.j2` are rendered as Jinja2 templates (the `.j2`
        extension is stripped in the output). Other files are copied as-is.

        Returns the list of created files.
        """
        template_dir = self._templates_dir / template_name
        if not template_dir.exists():
            raise ScaffoldError(
                f"Template {template_name!r} not found in {self._templates_dir}. "
                f"Available: {self._list_templates()}"
            )

        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )

        project_path.mkdir(parents=True, exist_ok=True)
        created: list[Path] = []

        for template_path in sorted(template_dir.rglob("*")):
            if not template_path.is_file():
                continue

            rel = template_path.relative_to(template_dir)
            rel_str = str(rel)

            # Determine output path (strip .j2 suffix if present)
            if rel_str.endswith(".j2"):
                out_rel = Path(rel_str[:-3])
                rendered = env.get_template(rel_str).render(**context)
                content: bytes | str = rendered
                mode = "w"
            else:
                out_rel = rel
                content = template_path.read_bytes()
                mode = "wb"

            out_path = project_path / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)

            if mode == "w":
                out_path.write_text(str(content), encoding="utf-8")
            else:
                out_path.write_bytes(bytes(content))  # type: ignore[arg-type]

            created.append(out_path)
            log.debug("scaffold_file_created", path=str(out_rel))

        log.info(
            "scaffold_complete",
            template=template_name,
            project=str(project_path),
            files=len(created),
        )
        return created

    def _list_templates(self) -> list[str]:
        if not self._templates_dir.exists():
            return []
        return sorted(d.name for d in self._templates_dir.iterdir() if d.is_dir())

    def list_templates(self) -> list[str]:
        return self._list_templates()
