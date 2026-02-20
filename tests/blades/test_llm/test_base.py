"""Tests for the LLM blade Protocol and ABC."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from jackknife.blades.llm.base import BaseLLMProvider, LLMProviderProtocol
from jackknife.blades.llm.models import LLMRequest, LLMResponse, StreamChunk
from jackknife.core.exceptions import ConfigurationError


class MockLLMProvider(BaseLLMProvider):
    """Minimal mock LLM provider for testing the interface."""

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="mock response",
            model="mock-model",
            provider="mock",
        )

    def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        async def _gen() -> AsyncIterator[StreamChunk]:
            yield StreamChunk(content="mock ")
            yield StreamChunk(content="stream", finish_reason="stop")

        return _gen()


def test_mock_satisfies_protocol() -> None:
    """MockLLMProvider should satisfy LLMProviderProtocol."""
    mock = MockLLMProvider()
    assert isinstance(mock, LLMProviderProtocol)


async def test_complete_returns_response() -> None:
    mock = MockLLMProvider()
    request = LLMRequest(messages=[{"role": "user", "content": "hello"}])
    response = await mock.complete(request)
    assert response.content == "mock response"
    assert response.model == "mock-model"


async def test_embed_raises_not_implemented() -> None:
    """Embedding is optional — base raises NotImplementedError."""
    mock = MockLLMProvider()
    with pytest.raises(NotImplementedError):
        await mock.embed(["test text"])


async def test_health_check_returns_true_for_working_provider() -> None:
    mock = MockLLMProvider()
    result = await mock.health_check()
    assert result is True


def test_factory_raises_configuration_error_for_unknown_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from jackknife.blades.llm.factory import create_llm
    from jackknife.core.config import get_settings

    monkeypatch.setenv("LLM_PROVIDER", "unknown-provider")
    get_settings.cache_clear()
    settings = get_settings()
    with pytest.raises(ConfigurationError, match="Unknown LLM provider"):
        create_llm(settings)
