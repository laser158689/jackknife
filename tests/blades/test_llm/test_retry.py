"""Tests for RetryingLLMProvider."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest

from jackknife.blades.llm.base import BaseLLMProvider
from jackknife.blades.llm.models import LLMRequest, LLMResponse, StreamChunk
from jackknife.blades.llm.retry import RetryingLLMProvider
from jackknife.core.exceptions import LLMConnectionError, LLMRateLimitError, LLMResponseError


class _FakeProvider(BaseLLMProvider):
    def __init__(self, responses: list[LLMResponse | Exception]) -> None:
        self._responses = iter(responses)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        result = next(self._responses)
        if isinstance(result, Exception):
            raise result
        return result

    def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        async def _gen() -> AsyncIterator[StreamChunk]:
            yield StreamChunk(content="chunk")

        return _gen()


def _ok_response() -> LLMResponse:
    return LLMResponse(content="ok", model="mock", provider="mock")


async def test_succeeds_on_first_attempt() -> None:
    provider = RetryingLLMProvider(_FakeProvider([_ok_response()]))
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    result = await provider.complete(req)
    assert result.content == "ok"


async def test_retries_on_rate_limit_then_succeeds() -> None:
    provider = RetryingLLMProvider(
        _FakeProvider([LLMRateLimitError("rate limit"), _ok_response()]),
        max_attempts=3,
        base_delay=0,
    )
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    result = await provider.complete(req)
    assert result.content == "ok"


async def test_retries_on_connection_error_then_succeeds() -> None:
    provider = RetryingLLMProvider(
        _FakeProvider([LLMConnectionError("conn"), LLMConnectionError("conn"), _ok_response()]),
        max_attempts=3,
        base_delay=0,
    )
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    result = await provider.complete(req)
    assert result.content == "ok"


async def test_raises_after_max_attempts() -> None:
    provider = RetryingLLMProvider(
        _FakeProvider([LLMRateLimitError("x"), LLMRateLimitError("x"), LLMRateLimitError("x")]),
        max_attempts=3,
        base_delay=0,
    )
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    with pytest.raises(LLMRateLimitError):
        await provider.complete(req)


async def test_non_retryable_error_propagates_immediately() -> None:
    provider = RetryingLLMProvider(
        _FakeProvider([LLMResponseError("bad response")]),
        max_attempts=3,
        base_delay=0,
    )
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    with pytest.raises(LLMResponseError):
        await provider.complete(req)


async def test_stream_delegates_to_inner_provider() -> None:
    inner = cast(BaseLLMProvider, MagicMock(spec=BaseLLMProvider))

    async def _gen() -> AsyncIterator[StreamChunk]:
        yield StreamChunk(content="streamed")

    inner.stream = MagicMock(return_value=_gen())  # type: ignore[method-assign]
    provider = RetryingLLMProvider(inner)
    req = LLMRequest(messages=[{"role": "user", "content": "hi"}])
    chunks = [c async for c in provider.stream(req)]
    assert chunks[0].content == "streamed"
    inner.stream.assert_called_once_with(req)


async def test_embed_retries_on_rate_limit() -> None:
    inner = cast(BaseLLMProvider, MagicMock(spec=BaseLLMProvider))
    inner.embed = AsyncMock(side_effect=[LLMRateLimitError("rate"), [[0.1, 0.2]]])  # type: ignore[method-assign]
    provider = RetryingLLMProvider(inner, max_attempts=3, base_delay=0)
    result = await provider.embed(["text"])
    assert result == [[0.1, 0.2]]
    assert inner.embed.call_count == 2


async def test_health_check_delegates() -> None:
    inner = cast(BaseLLMProvider, MagicMock(spec=BaseLLMProvider))
    inner.health_check = AsyncMock(return_value=True)  # type: ignore[method-assign]
    provider = RetryingLLMProvider(inner)
    assert await provider.health_check() is True
