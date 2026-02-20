"""
LLM blade — Protocol and ABC definitions.

Design-first: define the interface before any implementation.
All LLM providers (OpenAI, Anthropic, Gemini, Ollama, etc.) must
satisfy this interface. litellm is used in the implementation layer
(Phase 3), but all application code depends only on these abstractions.

Two interface styles:
- LLMProviderProtocol: structural (duck typing). Any object with
  these methods satisfies the protocol without inheritance. Great for mocks.
- BaseLLMProvider: enforced via ABC. Inherit from this to get
  validation, error wrapping, and health_check for free.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable

from jackknife.blades.llm.models import LLMRequest, LLMResponse, StreamChunk


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """
    Structural protocol for LLM providers.

    Any object with complete() and stream() satisfies this protocol,
    even without inheriting BaseLLMProvider. Use for type hints and mocks.
    """

    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a non-streaming completion."""
        ...

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion tokens as they arrive."""
        ...

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        ...


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Inherit from this to build a provider implementation.
    The health_check default implementation calls complete() with a
    minimal message — override for a cheaper provider-specific check.
    """

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """Generate a non-streaming completion."""

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Stream completion tokens."""

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings. Not all providers support this.
        Override to add embedding support to a provider.
        """
        raise NotImplementedError(f"{self.__class__.__name__} does not support embeddings")

    async def health_check(self) -> bool:
        """Check if the provider is reachable."""
        try:
            await self.complete(
                LLMRequest(messages=[{"role": "user", "content": "ping"}], max_tokens=1)
            )
            return True
        except Exception:
            return False
