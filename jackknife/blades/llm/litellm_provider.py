"""
LLM blade — LiteLLM provider implementation.

LiteLLM provides a unified interface to 100+ LLM providers.
The model string selects the provider:

    "gpt-4o-mini"               → OpenAI
    "claude-3-5-sonnet-latest"  → Anthropic
    "gemini/gemini-2.0-flash"   → Google
    "ollama/llama3.2"           → Ollama (local)
    "groq/llama-3.1-70b"        → Groq

See: https://docs.litellm.ai/docs/providers
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from jackknife.blades.llm.base import BaseLLMProvider
from jackknife.blades.llm.models import LLMRequest, LLMResponse, StreamChunk
from jackknife.core.exceptions import LLMConnectionError, LLMRateLimitError, LLMResponseError
from jackknife.core.logging import get_logger

try:
    import litellm
except ImportError as exc:
    raise ImportError(
        "LiteLLM is not installed. Enable the llm extra: poetry install -E llm"
    ) from exc

log = get_logger(__name__)

# Silence litellm's verbose startup logging
litellm.suppress_debug_info = True


class LiteLLMProvider(BaseLLMProvider):
    """
    LiteLLM-backed provider. Supports any litellm-compatible model string.

    Pass api_key only if you can't use the standard environment variables
    (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.). Environment variables are
    the preferred approach.
    """

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: str | None = None,
    ) -> None:
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        if api_key:
            litellm.api_key = api_key

    def _raise_mapped(self, exc: Exception) -> None:
        msg = str(exc)
        lower = msg.lower()
        if "rate limit" in lower or "rate_limit" in lower:
            raise LLMRateLimitError(msg) from exc
        if any(x in lower for x in ("auth", "invalid key", "api key")):
            raise LLMConnectionError(msg) from exc
        raise LLMResponseError(msg) from exc

    def _build_kwargs(self, request: LLMRequest) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": request.model or self._model,
            "messages": request.messages,
            "temperature": request.temperature
            if request.temperature is not None
            else self._temperature,
            "max_tokens": request.max_tokens or self._max_tokens,
            **request.extra,
        }
        if request.response_format:
            kwargs["response_format"] = request.response_format
        return kwargs

    async def complete(self, request: LLMRequest) -> LLMResponse:
        kwargs = self._build_kwargs(request)
        model = str(kwargs["model"])
        try:
            resp = await litellm.acompletion(**kwargs)
        except Exception as exc:
            self._raise_mapped(exc)
            raise  # unreachable — satisfies mypy

        choice = resp.choices[0]
        content: str = getattr(choice.message, "content", "") or ""
        finish: str = getattr(choice, "finish_reason", None) or "stop"
        usage = getattr(resp, "usage", None)

        return LLMResponse(
            content=content,
            model=getattr(resp, "model", model) or model,
            provider=model.split("/")[0] if "/" in model else "openai",
            finish_reason=finish,  # type: ignore[arg-type]
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            total_tokens=getattr(usage, "total_tokens", 0) or 0,
            raw=dict(resp) if hasattr(resp, "__iter__") else {},
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[StreamChunk]:
        kwargs = self._build_kwargs(request)
        kwargs["stream"] = True
        try:
            response = await litellm.acompletion(**kwargs)
        except Exception as exc:
            self._raise_mapped(exc)
            raise  # unreachable

        index = 0
        async for chunk in response:
            delta = chunk.choices[0].delta
            content: str = getattr(delta, "content", "") or ""
            finish: str | None = getattr(chunk.choices[0], "finish_reason", None)
            yield StreamChunk(content=content, finish_reason=finish, index=index)
            index += 1

    async def embed(self, texts: list[str]) -> list[list[float]]:
        try:
            resp = await litellm.aembedding(model=self._model, input=texts)
            return [item["embedding"] for item in resp.data]
        except Exception as exc:
            self._raise_mapped(exc)
            raise  # unreachable
