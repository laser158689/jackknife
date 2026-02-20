"""Tests for TaskStatusRegistry."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from jackknife.blades.agents.models import TaskStatus
from jackknife.blades.agents.status import TaskStatusRegistry


async def test_set_and_get():
    reg = TaskStatusRegistry()
    task_id = uuid4()
    await reg.set(task_id, TaskStatus.RUNNING)
    status = await reg.get(task_id)
    assert status == TaskStatus.RUNNING


async def test_default_status_is_pending():
    reg = TaskStatusRegistry()
    status = await reg.get(uuid4())
    assert status == TaskStatus.PENDING


async def test_all_statuses():
    reg = TaskStatusRegistry()
    ids = [uuid4() for _ in range(3)]
    statuses = [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED]
    for tid, s in zip(ids, statuses, strict=False):
        await reg.set(tid, s)
    all_s = await reg.all_statuses()
    for tid, expected in zip(ids, statuses, strict=False):
        assert all_s[tid] == expected


async def test_count_by_status():
    reg = TaskStatusRegistry()
    for _ in range(3):
        await reg.set(uuid4(), TaskStatus.COMPLETED)
    for _ in range(2):
        await reg.set(uuid4(), TaskStatus.FAILED)
    counts = await reg.count_by_status()
    assert counts["completed"] == 3
    assert counts["failed"] == 2


async def test_concurrent_updates_are_safe():
    reg = TaskStatusRegistry()
    task_id = uuid4()

    async def update(status: TaskStatus) -> None:
        await reg.set(task_id, status)

    await asyncio.gather(
        update(TaskStatus.RUNNING),
        update(TaskStatus.COMPLETED),
        update(TaskStatus.RUNNING),
    )
    # Final status should be one of the set values (not corrupted)
    final = await reg.get(task_id)
    assert final in {TaskStatus.RUNNING, TaskStatus.COMPLETED}
