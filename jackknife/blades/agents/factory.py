"""Agents blade — factory functions."""

from __future__ import annotations

from jackknife.blades.agents.orchestrator import Orchestrator
from jackknife.blades.agents.worker import EchoWorker, LLMWorker


def create_orchestrator(max_parallel: int = 1) -> Orchestrator:
    """
    Create an Orchestrator with the given parallelism level.

    max_parallel=1  — serial execution (safe default)
    max_parallel=N  — up to N independent tasks run concurrently
    """
    return Orchestrator(max_parallel=max_parallel)


def create_echo_worker() -> EchoWorker:
    """Create an EchoWorker for testing orchestration logic."""
    return EchoWorker()


def create_llm_worker(provider: object, system_prompt: str | None = None) -> LLMWorker:
    """
    Create a worker that processes tasks using an LLM provider.

    provider must be a BaseLLMProvider instance (e.g. LiteLLMProvider).
    """
    return LLMWorker(provider=provider, system_prompt=system_prompt)
