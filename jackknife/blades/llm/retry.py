"""
LLM blade — retry and backoff utilities.

Wraps any BaseLLMProvider with exponential backoff on transient errors
(rate limits, connection failures). Uses only stdlib — no tenacity dependency.

Usage:
    from jackknife.blades.llm.retry import RetryingLLMProvider

    base = create_llm(settings)
    llm  = RetryingLLMProvider(base, max_attempts=4, base_delay=1.0)
    response = await llm.complete(request)
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator

from jackknife.blades.llm.base import BaseLLMProvider
from jackknife.blades.llm.models import LLMRequest, LLMResponse, StreamChunk
from jackknife.core.exceptions import LLMConnectionError, LLMRateLimitError

logger = logging.getLogger(__name__)

# Errors that are worth retrying
_RETRYABLE = (LLMRateLimitError, LLMConnectionError)


class RetryingLLMProvider(BaseLLMProvider):
    """
    Decorator that adds exponential backoff retries to any LLM provider.

    Retries on LLMRateLimitError and LLMConnectionError.
    Other exceptions propagate immediately.

    Args:
        provider:     The wrapped provider.
        max_attempts: Total attempts (including the first). Default 3.
        base_delay:   Initial wait in seconds before first retry. Default 1.0.
        max_delay:    Cap on per-attempt wait. Default 60.0.
        backoff:      Multiplier applied after each failure. Default 2.0.
    """

    def __init__(
        self,
        provider: BaseLLMProvider,
        *,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff: float = 2.0,
    ) -> None:
        self._provider = provider
        self._max_attempts = max_attempts
        self._base_delay = base_delay
        self._max_delay = max_delay
        self._backoff = backoff

    async def complete(self, request: LLMRequest) -> LLMResponse:
        delay = self._base_delay
        last_exc: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return await self._provider.complete(request)
            except _RETRYABLE as exc:
                last_exc = exc
                if attempt == self._max_attempts:
                    break
                logger.warning(
                    "LLM transient error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt,
                    self._max_attempts,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * self._backoff, self._max_delay)
        raise last_exc  # type: ignore[misc]

    def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        """Streaming is not retried — delegate directly to the inner provider."""
        return self._provider.stream(request)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        delay = self._base_delay
        last_exc: Exception | None = None
        for attempt in range(1, self._max_attempts + 1):
            try:
                return await self._provider.embed(texts)
            except _RETRYABLE as exc:
                last_exc = exc
                if attempt == self._max_attempts:
                    break
                logger.warning(
                    "LLM embed transient error (attempt %d/%d), retrying in %.1fs: %s",
                    attempt,
                    self._max_attempts,
                    delay,
                    exc,
                )
                await asyncio.sleep(delay)
                delay = min(delay * self._backoff, self._max_delay)
        raise last_exc  # type: ignore[misc]

    async def health_check(self) -> bool:
        return await self._provider.health_check()
