"""Agents blade — Pydantic models."""

from __future__ import annotations

from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import Field

from jackknife.core.models import JackknifeBaseModel, TimestampedModel


class TaskStatus(str, Enum):
    """Possible states for a task in the orchestrator."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"  # Skipped because a dependency failed


class Task(TimestampedModel):
    """A unit of work assigned to a worker agent."""

    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    task_type: str = "general"  # Used to route to the right worker
    status: TaskStatus = TaskStatus.PENDING
    depends_on: list[UUID] = Field(default_factory=list)  # Task IDs that must complete first
    assigned_to: str | None = None  # Worker agent name
    context: dict[str, Any] = Field(default_factory=dict)  # Input context for the worker
    priority: int = 0  # Higher = higher priority


class TaskResult(TimestampedModel):
    """The result of a completed task."""

    task_id: UUID
    status: TaskStatus
    summary: str = ""
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    memory_keys: list[str] = Field(default_factory=list)  # Keys written to shared memory


class AgentMessage(JackknifeBaseModel):
    """A message passed between agents or from agent to orchestrator."""

    from_agent: str
    to_agent: str
    task_id: UUID | None = None
    content: str
    payload: dict[str, Any] = Field(default_factory=dict)
