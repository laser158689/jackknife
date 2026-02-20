"""LLM blade — Pydantic request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from jackknife.core.models import JackknifeBaseModel, TimestampedModel

Message = dict[str, str]  # {"role": "user"|"assistant"|"system", "content": "..."}


class LLMRequest(JackknifeBaseModel):
    """Request to an LLM provider."""

    messages: list[Message]
    model: str | None = None  # Override settings.llm.model if set
    temperature: float | None = None  # Override settings.llm.temperature if set
    max_tokens: int | None = None  # Override settings.llm.max_tokens if set
    stream: bool = False
    response_format: dict[str, Any] | None = None  # For structured output
    extra: dict[str, Any] = Field(default_factory=dict)  # Provider-specific params


class LLMResponse(TimestampedModel):
    """Response from an LLM provider."""

    content: str
    model: str
    provider: str
    finish_reason: Literal["stop", "length", "tool_calls", "error"] = "stop"
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    raw: dict[str, Any] = Field(default_factory=dict)  # Raw provider response


class StreamChunk(JackknifeBaseModel):
    """A single token/chunk from a streaming LLM response."""

    content: str
    finish_reason: str | None = None
    index: int = 0
