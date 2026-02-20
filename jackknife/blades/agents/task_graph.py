"""
Agents blade — task dependency graph.

Uses networkx to model tasks as a directed acyclic graph (DAG).
Topological sort determines execution order. Tasks with no remaining
unfulfilled dependencies are "ready" and can be dispatched immediately
(potentially in parallel).
"""

from __future__ import annotations

from uuid import UUID

from jackknife.blades.agents.models import Task, TaskStatus
from jackknife.core.exceptions import AgentError

try:
    import networkx as nx
except ImportError as exc:
    raise ImportError(
        "networkx is not installed. Enable the agents extra: poetry install -E agents"
    ) from exc


class TaskGraph:
    """
    DAG of Tasks with dependency tracking.

    Nodes are task UUIDs. Edges represent dependencies:
    an edge A → B means B depends on A (A must complete before B starts).
    """

    def __init__(self) -> None:
        self._graph: nx.DiGraph = nx.DiGraph()
        self._tasks: dict[UUID, Task] = {}

    def add_task(self, task: Task) -> None:
        """Register a task and its declared dependencies."""
        self._tasks[task.id] = task
        self._graph.add_node(task.id)
        for dep_id in task.depends_on:
            # Edge: dep_id → task.id (dep must finish before task starts)
            self._graph.add_edge(dep_id, task.id)

    def validate(self) -> None:
        """Raise AgentError if the graph contains cycles."""
        if not nx.is_directed_acyclic_graph(self._graph):
            raise AgentError("Task graph contains a cycle — cannot execute")

    def ready_tasks(self, completed: set[UUID]) -> list[Task]:
        """
        Return tasks that have all dependencies satisfied and are still PENDING.

        A task is ready when:
        - Its status is PENDING
        - All tasks in its depends_on set are in the completed set
        """
        ready: list[Task] = []
        for _task_id, task in self._tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            if all(dep in completed for dep in task.depends_on):
                ready.append(task)
        # Sort by priority descending, then by insertion order
        return sorted(ready, key=lambda t: -t.priority)

    def execution_order(self) -> list[Task]:
        """
        Return all tasks in a valid topological execution order.

        Tasks with no dependencies come first. Within a layer, tasks
        are sorted by priority (descending).
        """
        try:
            ordered_ids: list[UUID] = list(nx.topological_sort(self._graph))
        except nx.NetworkXUnfeasible as exc:
            raise AgentError(f"Cannot determine execution order: {exc}") from exc
        return [self._tasks[tid] for tid in ordered_ids if tid in self._tasks]

    def update_status(self, task_id: UUID, status: TaskStatus) -> None:
        """Update the status of a task in-place."""
        if task_id not in self._tasks:
            raise AgentError(f"Unknown task ID: {task_id}")
        self._tasks[task_id] = self._tasks[task_id].model_copy(update={"status": status})

    def is_complete(self) -> bool:
        """Return True when all tasks have reached a terminal status."""
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(t.status in terminal for t in self._tasks.values())

    def failed_tasks(self) -> list[Task]:
        return [t for t in self._tasks.values() if t.status == TaskStatus.FAILED]

    def completed_ids(self) -> set[UUID]:
        return {t.id for t in self._tasks.values() if t.status == TaskStatus.COMPLETED}

    def all_tasks(self) -> list[Task]:
        return list(self._tasks.values())

    def get_task(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    def __len__(self) -> int:
        return len(self._tasks)
