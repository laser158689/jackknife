"""Tests for TaskGraph."""

from __future__ import annotations

import pytest

from jackknife.blades.agents.models import Task, TaskStatus
from jackknife.blades.agents.task_graph import TaskGraph
from jackknife.core.exceptions import AgentError


def make_task(title: str, depends_on: list | None = None, priority: int = 0) -> Task:
    return Task(title=title, description=title, depends_on=depends_on or [], priority=priority)


def test_add_task_and_execution_order():
    graph = TaskGraph()
    t1 = make_task("task1")
    t2 = make_task("task2", depends_on=[t1.id])
    graph.add_task(t1)
    graph.add_task(t2)
    order = graph.execution_order()
    assert order[0].id == t1.id
    assert order[1].id == t2.id


def test_ready_tasks_with_no_dependencies():
    graph = TaskGraph()
    t1 = make_task("independent1")
    t2 = make_task("independent2")
    graph.add_task(t1)
    graph.add_task(t2)
    ready = graph.ready_tasks(completed=set())
    assert len(ready) == 2


def test_ready_tasks_blocked_by_dependency():
    graph = TaskGraph()
    t1 = make_task("first")
    t2 = make_task("second", depends_on=[t1.id])
    graph.add_task(t1)
    graph.add_task(t2)
    # With nothing completed, only t1 is ready
    ready = graph.ready_tasks(completed=set())
    assert len(ready) == 1
    assert ready[0].id == t1.id
    # Simulate orchestrator: mark t1 as completed, then check ready
    from jackknife.blades.agents.models import TaskStatus

    graph.update_status(t1.id, TaskStatus.COMPLETED)
    ready2 = graph.ready_tasks(completed={t1.id})
    assert len(ready2) == 1
    assert ready2[0].id == t2.id


def test_priority_ordering():
    graph = TaskGraph()
    low = make_task("low", priority=0)
    high = make_task("high", priority=10)
    graph.add_task(low)
    graph.add_task(high)
    ready = graph.ready_tasks(completed=set())
    assert ready[0].id == high.id


def test_validate_raises_on_cycle():
    graph = TaskGraph()
    t1 = make_task("t1")
    t2 = make_task("t2", depends_on=[t1.id])
    # Manually create a cycle by adding t1 depending on t2
    t1_cyclic = Task(id=t1.id, title="t1", description="t1", depends_on=[t2.id])
    graph.add_task(t1_cyclic)
    graph.add_task(t2)
    with pytest.raises(AgentError, match="cycle"):
        graph.validate()


def test_update_status():
    graph = TaskGraph()
    t = make_task("task")
    graph.add_task(t)
    graph.update_status(t.id, TaskStatus.RUNNING)
    assert graph.get_task(t.id).status == TaskStatus.RUNNING  # type: ignore[union-attr]


def test_is_complete():
    graph = TaskGraph()
    t = make_task("task")
    graph.add_task(t)
    assert not graph.is_complete()
    graph.update_status(t.id, TaskStatus.COMPLETED)
    assert graph.is_complete()


def test_completed_ids():
    graph = TaskGraph()
    t1 = make_task("t1")
    t2 = make_task("t2")
    graph.add_task(t1)
    graph.add_task(t2)
    graph.update_status(t1.id, TaskStatus.COMPLETED)
    assert t1.id in graph.completed_ids()
    assert t2.id not in graph.completed_ids()


def test_len():
    graph = TaskGraph()
    assert len(graph) == 0
    graph.add_task(make_task("t"))
    assert len(graph) == 1
