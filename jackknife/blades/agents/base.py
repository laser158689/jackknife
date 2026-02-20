"""
Agents blade — Protocol and ABC definitions.

Implements the orchestrator + worker pattern for multi-agent development.

Pattern:
    Orchestrator decomposes a goal into a task DAG (directed acyclic graph).
    Workers are stateless — they read context from shared memory and write
    results back. This makes workers safe to parallelize.

    Memory is the shared nervous system:
    - Orchestrator reads task context from memory before decomposing
    - Workers read prior results from memory before executing
    - Workers write results to memory after completing
    - Next dependent task picks up results automatically

    The memory MCP server exposes this store to all tools:
    Claude Code, Cursor, Windsurf, and custom agents all share one store.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from jackknife.blades.agents.models import Task, TaskResult, TaskStatus


@runtime_checkable
class AgentProtocol(Protocol):
    """Structural protocol — any object with run() is an agent."""

    async def run(self, task: Task) -> TaskResult:
        """Execute a task and return the result."""
        ...


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    name: str = "base_agent"
    description: str = "Base agent"

    @abstractmethod
    async def run(self, task: Task) -> TaskResult:
        """Execute a task."""

    async def on_error(self, task: Task, error: Exception) -> TaskResult | None:
        """
        Called when run() raises an exception.

        Return a TaskResult to handle the error gracefully,
        or return None to re-raise the original error.
        """
        return None


class BaseOrchestratorAgent(BaseAgent):
    """
    Orchestrator: decomposes goals into a task DAG, assigns workers,
    tracks status, and aggregates results.

    Task graph rules:
    - Tasks are nodes; dependencies are directed edges (A → B means B needs A first)
    - A task cannot start until all its dependencies have COMPLETED status
    - Failed tasks propagate failure to dependents by default
    - All results are written to shared memory after each task completes
    """

    @abstractmethod
    async def decompose(self, goal: str) -> list[Task]:
        """
        Break a high-level goal into concrete tasks.
        Returns tasks with dependency relationships set.
        """

    @abstractmethod
    async def assign(self, task: Task) -> BaseAgent:
        """Select the appropriate worker agent for a given task."""

    @abstractmethod
    async def get_status(self) -> dict[str, TaskStatus]:
        """Return current status of all tasks, keyed by task_id."""


class BaseWorkerAgent(BaseAgent):
    """
    Worker: executes a single focused task.

    Workers are stateless — all context comes from the task payload
    and shared memory. This makes them safe to run in parallel.
    """

    @abstractmethod
    async def run(self, task: Task) -> TaskResult:
        """
        Execute the assigned task.

        Pattern:
            1. Read any needed context from shared memory
            2. Perform the task
            3. Write results back to shared memory
            4. Return TaskResult with status and summary
        """

    def can_handle(self, task: Task) -> bool:
        """
        Return True if this worker can handle the given task type.
        Override to restrict which tasks this worker accepts.
        """
        return True
