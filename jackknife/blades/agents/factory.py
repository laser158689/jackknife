"""Agents blade — factory function."""

from __future__ import annotations

from jackknife.blades.agents.base import BaseOrchestratorAgent


def create_orchestrator() -> BaseOrchestratorAgent:
    """
    Create an orchestrator agent.

    Phase 6 will wire in the networkx-based task graph orchestrator.
    """
    raise NotImplementedError(
        "Agent blade implementation coming in Phase 6. "
        "Interface is defined — see jackknife/blades/agents/base.py"
    )
