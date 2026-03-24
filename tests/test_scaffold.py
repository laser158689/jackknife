"""Tests for scaffold engine and validators."""

from __future__ import annotations

import pytest

from jackknife.core.exceptions import ScaffoldError
from jackknife.scaffold.engine import ScaffoldEngine
from jackknife.scaffold.validators import (
    validate_output_dir,
    validate_project_name,
    validate_template,
)


class TestValidators:
    def test_valid_name(self):
        assert validate_project_name("my_project") == "my_project"

    def test_name_normalized(self):
        assert validate_project_name("My-Project") == "my_project"

    def test_empty_name_raises(self):
        with pytest.raises(ScaffoldError):
            validate_project_name("")

    def test_reserved_name_raises(self):
        with pytest.raises(ScaffoldError, match="reserved"):
            validate_project_name("jackknife")

    def test_name_starting_with_digit_raises(self):
        with pytest.raises(ScaffoldError):
            validate_project_name("1bad")

    def test_valid_output_dir(self, tmp_path):
        path = validate_output_dir(str(tmp_path), "my_project")
        assert path == tmp_path / "my_project"

    def test_output_dir_missing_raises(self):
        with pytest.raises(ScaffoldError, match="does not exist"):
            validate_output_dir("/nonexistent/path/abc", "proj")

    def test_existing_project_dir_raises(self, tmp_path):
        (tmp_path / "existing").mkdir()
        with pytest.raises(ScaffoldError, match="already exists"):
            validate_output_dir(str(tmp_path), "existing")

    def test_valid_templates(self):
        assert validate_template("streamlit") == "streamlit"
        assert validate_template("api") == "api"

    def test_invalid_template_raises(self):
        with pytest.raises(ScaffoldError, match="Unknown template"):
            validate_template("django")


class TestScaffoldEngine:
    def test_list_templates(self):
        engine = ScaffoldEngine()
        templates = engine.list_templates()
        assert "streamlit" in templates
        assert "api" in templates

    def test_render_streamlit_project(self, tmp_path):
        engine = ScaffoldEngine()
        project_path = tmp_path / "myapp"
        context = {
            "project_name": "myapp",
            "project_name_title": "My App",
            "template": "streamlit",
        }
        created = engine.render_project("streamlit", project_path, context)
        assert len(created) > 0
        # Check key files were created
        assert (project_path / "main.py").exists()
        assert (project_path / "pyproject.toml").exists()
        assert (project_path / "CLAUDE.md").exists()

    def test_render_api_project(self, tmp_path):
        engine = ScaffoldEngine()
        project_path = tmp_path / "myapi"
        context = {
            "project_name": "myapi",
            "project_name_title": "My API",
            "template": "api",
        }
        created = engine.render_project("api", project_path, context)
        assert len(created) > 0
        assert (project_path / "main.py").exists()

    def test_template_content_contains_project_name(self, tmp_path):
        engine = ScaffoldEngine()
        project_path = tmp_path / "testproject"
        context = {
            "project_name": "testproject",
            "project_name_title": "Test Project",
            "template": "streamlit",
        }
        engine.render_project("streamlit", project_path, context)
        main_content = (project_path / "main.py").read_text()
        assert "Test Project" in main_content

    def test_unknown_template_raises(self, tmp_path):
        engine = ScaffoldEngine()
        with pytest.raises(ScaffoldError, match="not found"):
            engine.render_project("unknown", tmp_path / "p", {})

    def test_missing_templates_dir_raises(self, tmp_path):
        """Covers line 35: ScaffoldError when templates_dir doesn't exist."""
        with pytest.raises(ScaffoldError, match="Templates directory not found"):
            ScaffoldEngine(templates_dir=tmp_path / "nonexistent")

    def test_binary_file_copied_as_is(self, tmp_path):
        """Covers lines 84-86, 94: non-.j2 files are copied as binary."""
        templates_dir = tmp_path / "templates"
        tpl_dir = templates_dir / "mytpl"
        tpl_dir.mkdir(parents=True)
        binary_file = tpl_dir / "icon.bin"
        binary_file.write_bytes(b"\x00\x01\x02\x03")

        engine = ScaffoldEngine(templates_dir=templates_dir)
        project = tmp_path / "output"
        created = engine.render_project("mytpl", project, {})

        assert len(created) == 1
        assert (project / "icon.bin").read_bytes() == b"\x00\x01\x02\x03"

    def test_list_templates_missing_dir(self, tmp_path):
        """Covers line 109: _list_templates returns [] when dir is gone."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        engine = ScaffoldEngine(templates_dir=templates_dir)
        templates_dir.rmdir()
        assert engine._list_templates() == []
