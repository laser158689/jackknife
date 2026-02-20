"""Tests for the agents blade Protocol and ABC."""

from __future__ import annotations

from jackknife.blades.agents.base import AgentProtocol, BaseWorkerAgent
from jackknife.blades.agents.models import Task, TaskResult, TaskStatus


class MockWorker(BaseWorkerAgent):
    """Minimal mock worker for testing the interface."""

    name = "mock_worker"
    description = "A mock worker for tests"

    async def run(self, task: Task) -> TaskResult:
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            summary=f"Completed: {task.title}",
        )


def test_mock_worker_satisfies_protocol() -> None:
    worker = MockWorker()
    assert isinstance(worker, AgentProtocol)


async def test_worker_run_returns_result() -> None:
    worker = MockWorker()
    task = Task(title="Write tests", description="Write unit tests for the memory blade")
    result = await worker.run(task)
    assert result.status == TaskStatus.COMPLETED
    assert result.task_id == task.id


def test_worker_can_handle_defaults_true() -> None:
    """can_handle should return True by default."""
    worker = MockWorker()
    task = Task(title="Any task", description="Some task")
    assert worker.can_handle(task) is True


def test_task_model_defaults() -> None:
    task = Task(title="Test", description="A test task")
    assert task.status == TaskStatus.PENDING
    assert task.depends_on == []
    assert task.priority == 0


def test_task_result_model() -> None:
    task = Task(title="Test", description="test")
    result = TaskResult(task_id=task.id, status=TaskStatus.FAILED, error="Something went wrong")
    assert result.status == TaskStatus.FAILED
    assert result.error == "Something went wrong"
