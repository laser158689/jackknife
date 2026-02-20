"""
Agents blade — thread-safe task status registry.

asyncio.Lock ensures status updates from concurrent worker tasks
don't overwrite each other. The registry is a shared mutable object
owned by the orchestrator.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

from jackknife.blades.agents.models import TaskStatus
from jackknife.core.logging import get_logger

log = get_logger(__name__)


class TaskStatusRegistry:
    """
    Asyncio-safe registry of task statuses.

    The orchestrator passes this to all workers so they can report
    status without calling back into the orchestrator directly.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._statuses: dict[UUID, TaskStatus] = {}

    async def set(self, task_id: UUID, status: TaskStatus) -> None:
        """Update a task's status under the lock."""
        async with self._lock:
            prev = self._statuses.get(task_id)
            self._statuses[task_id] = status
            log.debug(
                "task_status_updated",
                task_id=str(task_id),
                prev=prev.value if prev else None,
                status=status.value,
            )

    async def get(self, task_id: UUID) -> TaskStatus:
        """Return the current status of a task (defaults to PENDING)."""
        async with self._lock:
            return self._statuses.get(task_id, TaskStatus.PENDING)

    async def all_statuses(self) -> dict[UUID, TaskStatus]:
        """Snapshot of all current statuses."""
        async with self._lock:
            return dict(self._statuses)

    async def count_by_status(self) -> dict[str, int]:
        """Return counts grouped by status value."""
        async with self._lock:
            counts: dict[str, int] = {}
            for status in self._statuses.values():
                counts[status.value] = counts.get(status.value, 0) + 1
            return counts
