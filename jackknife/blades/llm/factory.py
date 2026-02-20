"""LLM blade — factory function."""

from __future__ import annotations

from jackknife.blades.llm.base import BaseLLMProvider
from jackknife.core.config import Settings
from jackknife.core.exceptions import ConfigurationError


def create_llm(settings: Settings) -> BaseLLMProvider:
    """
    Create an LLM provider from settings.

    Phase 3 will wire in the litellm adapter. For now, raises
    NotImplementedError so the interface is established but the
    implementation is clearly pending.

    Args:
        settings: Application settings (uses settings.llm.provider)

    Returns:
        A BaseLLMProvider implementation

    Raises:
        ConfigurationError: If the provider name is not recognized
        NotImplementedError: Until Phase 3 is implemented
    """
    supported = {"openai", "anthropic", "gemini", "ollama", "azure"}

    if settings.llm.provider not in supported:
        raise ConfigurationError(
            f"Unknown LLM provider: {settings.llm.provider!r}. " f"Supported: {sorted(supported)}"
        )

    # Phase 3: wire in litellm adapter
    raise NotImplementedError(
        "LLM blade implementation coming in Phase 3. "
        "Provider interface is defined — see jackknife/blades/llm/base.py"
    )
