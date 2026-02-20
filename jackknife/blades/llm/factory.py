"""LLM blade — factory function."""

from __future__ import annotations

from jackknife.blades.llm.base import BaseLLMProvider
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError

_SUPPORTED = {"litellm"}


def create_llm(settings: Settings) -> BaseLLMProvider:
    """
    Create an LLM provider from settings.

    Requires the llm extra: poetry install -E llm
    Set LLM_PROVIDER=litellm (default) and LLM_MODEL=<model-string>.
    """
    provider = settings.llm.provider.lower()
    if provider not in _SUPPORTED:
        raise ConfigurationError(
            f"Unknown LLM provider: {provider!r}. Supported: {sorted(_SUPPORTED)}"
        )

    from jackknife.blades.llm.litellm_provider import LiteLLMProvider

    return LiteLLMProvider(
        model=settings.llm.model,
        temperature=settings.llm.temperature,
        max_tokens=settings.llm.max_tokens,
        api_key=settings.llm.api_key or None,
    )
