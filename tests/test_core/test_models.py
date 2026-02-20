"""Tests for shared Pydantic base models."""

from __future__ import annotations

from datetime import UTC

import pytest
from pydantic import ValidationError as PydanticValidationError

from jackknife.core.models import IdentifiedModel, JackknifeBaseModel, Metadata, TimestampedModel


def test_jackknife_base_model_forbids_extra_fields() -> None:
    """extra='forbid' catches config typos at validation time."""

    class MyModel(JackknifeBaseModel):
        name: str

    with pytest.raises(PydanticValidationError):
        MyModel(name="test", unexpected_field="oops")  # type: ignore[call-arg]


def test_jackknife_base_model_strips_whitespace() -> None:
    class MyModel(JackknifeBaseModel):
        name: str

    m = MyModel(name="  hello  ")
    assert m.name == "hello"


def test_timestamped_model_has_utc_timestamps() -> None:
    m = TimestampedModel()
    assert m.created_at.tzinfo == UTC
    assert m.updated_at.tzinfo == UTC


def test_identified_model_has_uuid() -> None:
    m1 = IdentifiedModel()
    m2 = IdentifiedModel()
    assert m1.id != m2.id  # Each instance gets a unique UUID


def test_metadata_allows_extra_fields() -> None:
    """Metadata uses extra='allow' for flexible key-value storage."""
    m = Metadata(source="test", custom_field="value")  # type: ignore[call-arg]
    assert m.source == "test"


def test_metadata_tags_default_to_empty_list() -> None:
    m = Metadata()
    assert m.tags == []
