"""Agents blade — orchestrator and worker agent patterns."""

from jackknife.blades.agents.base import (
    AgentProtocol,
    BaseAgent,
    BaseOrchestratorAgent,
    BaseWorkerAgent,
)
from jackknife.blades.agents.factory import create_orchestrator
from jackknife.blades.agents.models import AgentMessage, Task, TaskResult, TaskStatus

__all__ = [
    "AgentProtocol",
    "BaseAgent",
    "BaseOrchestratorAgent",
    "BaseWorkerAgent",
    "create_orchestrator",
    "Task",
    "TaskResult",
    "TaskStatus",
    "AgentMessage",
]
