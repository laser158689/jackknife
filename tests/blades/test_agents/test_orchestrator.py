"""Tests for Orchestrator and workers."""

from __future__ import annotations

from jackknife.blades.agents.factory import create_orchestrator
from jackknife.blades.agents.models import Task, TaskStatus
from jackknife.blades.agents.task_graph import TaskGraph
from jackknife.blades.agents.worker import EchoWorker


def make_task(title: str, depends_on: list | None = None) -> Task:
    return Task(title=title, description=f"Description of {title}", depends_on=depends_on or [])


async def test_orchestrator_runs_single_task():
    orch = create_orchestrator()
    worker = EchoWorker()
    orch.register_worker(worker)

    task = make_task("Echo task")
    result = await orch.run(task)
    assert result.status == TaskStatus.COMPLETED
    assert "Echo" in result.summary


async def test_orchestrator_runs_task_graph_in_order():
    orch = create_orchestrator()
    worker = EchoWorker()
    orch.register_worker(worker)

    t1 = make_task("first")
    t2 = make_task("second", depends_on=[t1.id])
    t3 = make_task("third", depends_on=[t2.id])

    graph = TaskGraph()
    for t in [t1, t2, t3]:
        graph.add_task(t)

    results = await orch.run_graph(graph)
    assert len(results) == 3
    assert all(r.status == TaskStatus.COMPLETED for r in results.values())


async def test_orchestrator_parallel_independent_tasks():
    orch = create_orchestrator(max_parallel=3)
    worker = EchoWorker()
    orch.register_worker(worker)

    tasks = [make_task(f"parallel_{i}") for i in range(5)]
    graph = TaskGraph()
    for t in tasks:
        graph.add_task(t)

    results = await orch.run_graph(graph)
    assert len(results) == 5
    assert all(r.status == TaskStatus.COMPLETED for r in results.values())


async def test_orchestrator_propagates_failure():
    from jackknife.blades.agents.base import BaseWorkerAgent
    from jackknife.blades.agents.models import TaskResult

    class FailingWorker(BaseWorkerAgent):
        name = "failing"
        description = "always fails"

        async def run(self, task: Task) -> TaskResult:
            raise RuntimeError("Intentional failure")

    orch = create_orchestrator()
    orch.register_worker(FailingWorker())

    t1 = make_task("will_fail")
    t2 = make_task("depends_on_fail", depends_on=[t1.id])

    graph = TaskGraph()
    graph.add_task(t1)
    graph.add_task(t2)

    results = await orch.run_graph(graph)
    assert results[t1.id].status == TaskStatus.FAILED
    # t2 should be SKIPPED because t1 failed
    assert graph.get_task(t2.id).status == TaskStatus.SKIPPED  # type: ignore[union-attr]


async def test_echo_worker_output():
    worker = EchoWorker()
    task = make_task("Test echo")
    result = await worker.run(task)
    assert result.status == TaskStatus.COMPLETED
    assert result.output["title"] == "Test echo"


async def test_get_status_returns_dict():
    orch = create_orchestrator()
    worker = EchoWorker()
    orch.register_worker(worker)
    task = make_task("status_test")
    await orch.run(task)
    status = await orch.get_status()
    assert isinstance(status, dict)
