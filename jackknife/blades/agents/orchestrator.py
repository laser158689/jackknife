"""
Agents blade — orchestrator implementation.

The orchestrator:
1. Accepts a task graph (TaskGraph)
2. Dispatches ready tasks to registered workers
3. Tracks status in TaskStatusRegistry
4. Propagates failures to dependent tasks
5. Writes results to shared memory when a store is configured
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from jackknife.blades.agents.base import BaseOrchestratorAgent, BaseWorkerAgent
from jackknife.blades.agents.models import Task, TaskResult, TaskStatus
from jackknife.blades.agents.status import TaskStatusRegistry
from jackknife.blades.agents.task_graph import TaskGraph
from jackknife.core.exceptions import OrchestratorError
from jackknife.core.logging import get_logger

log = get_logger(__name__)


class Orchestrator(BaseOrchestratorAgent):
    """
    Concrete orchestrator that executes a TaskGraph using registered workers.

    Workers are registered by task_type. When a task becomes ready,
    the orchestrator finds a matching worker and dispatches it.
    If max_parallel > 1, independent tasks run concurrently.
    """

    name: str = "orchestrator"
    description: str = "Dispatches tasks to registered workers"

    def __init__(self, max_parallel: int = 1) -> None:
        self._workers: dict[str, BaseWorkerAgent] = {}
        self._default_worker: BaseWorkerAgent | None = None
        self._max_parallel = max_parallel
        self._registry = TaskStatusRegistry()

    def register_worker(self, worker: BaseWorkerAgent, task_types: list[str] | None = None) -> None:
        """
        Register a worker for specific task types.
        If task_types is None or empty, the worker becomes the default.
        """
        if task_types:
            for t in task_types:
                self._workers[t] = worker
        else:
            self._default_worker = worker

    def _find_worker(self, task: Task) -> BaseWorkerAgent:
        worker = self._workers.get(task.task_type) or self._default_worker
        if worker is None:
            raise OrchestratorError(
                f"No worker registered for task_type={task.task_type!r}. "
                f"Registered types: {list(self._workers)}"
            )
        return worker

    async def run(self, task: Task) -> TaskResult:
        """
        Entry point: treat the single task as a one-task graph.
        For multi-task execution, call run_graph() directly.
        """
        graph = TaskGraph()
        graph.add_task(task)
        results = await self.run_graph(graph)
        return results[task.id]

    async def run_graph(self, graph: TaskGraph) -> dict[UUID, TaskResult]:
        """Execute all tasks in the graph and return results keyed by task ID."""
        graph.validate()
        results: dict[UUID, TaskResult] = {}
        completed: set[UUID] = set()

        while not graph.is_complete():
            ready = graph.ready_tasks(completed)
            if not ready:
                if not graph.is_complete():
                    raise OrchestratorError(
                        "Deadlock: no ready tasks but graph is not complete. "
                        "Check for unresolvable dependencies."
                    )
                break

            batch = ready[: self._max_parallel]
            tasks_coros = [self._dispatch(task, graph) for task in batch]
            batch_results: list[TaskResult] = await asyncio.gather(*tasks_coros)

            for task, result in zip(batch, batch_results, strict=False):
                results[task.id] = result
                if result.status == TaskStatus.COMPLETED:
                    completed.add(task.id)
                    graph.update_status(task.id, TaskStatus.COMPLETED)
                else:
                    graph.update_status(task.id, TaskStatus.FAILED)
                    await self._propagate_failure(task.id, graph)

        return results

    async def _dispatch(self, task: Task, graph: TaskGraph) -> TaskResult:
        """Dispatch a single task to its worker."""
        await self._registry.set(task.id, TaskStatus.RUNNING)
        graph.update_status(task.id, TaskStatus.RUNNING)
        log.info("task_dispatched", task_id=str(task.id), title=task.title)
        try:
            worker = self._find_worker(task)
            result = await worker.run(task)
        except Exception as exc:
            log.error("task_failed", task_id=str(task.id), error=str(exc))
            result = TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(exc),
            )
        await self._registry.set(task.id, result.status)
        log.info(
            "task_complete",
            task_id=str(task.id),
            status=result.status.value,
        )
        return result

    async def _propagate_failure(self, failed_id: UUID, graph: TaskGraph) -> None:
        """Mark all transitive dependents of a failed task as SKIPPED."""
        for task in graph.all_tasks():
            if failed_id in task.depends_on and task.status == TaskStatus.PENDING:
                graph.update_status(task.id, TaskStatus.SKIPPED)
                await self._registry.set(task.id, TaskStatus.SKIPPED)
                await self._propagate_failure(task.id, graph)

    async def decompose(self, goal: str) -> list[Task]:
        """Override in subclasses to decompose a goal into tasks."""
        raise NotImplementedError(
            "Subclass Orchestrator and implement decompose() to break goals into tasks"
        )

    async def assign(self, task: Task) -> BaseWorkerAgent:
        """Return the registered worker for a task type."""
        return self._find_worker(task)

    async def get_status(self) -> dict[str, TaskStatus]:
        all_statuses = await self._registry.all_statuses()
        return {str(k): v for k, v in all_statuses.items()}
