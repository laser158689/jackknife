"""
Agents blade — worker implementations.

Workers are stateless — all context comes from the task payload
and optionally shared memory. This makes them safe to run in parallel.

Two provided implementations:
- EchoWorker: testing/demo worker that echoes back task info
- LLMWorker: worker that calls an LLM provider to process the task
"""

from __future__ import annotations

from jackknife.blades.agents.base import BaseWorkerAgent
from jackknife.blades.agents.models import Task, TaskResult, TaskStatus
from jackknife.core.logging import get_logger

log = get_logger(__name__)


class EchoWorker(BaseWorkerAgent):
    """
    Simple worker that echoes the task description as its result.
    Useful for testing orchestration logic without real side effects.
    """

    name: str = "echo_worker"
    description: str = "Returns task title and description as output"

    async def run(self, task: Task) -> TaskResult:
        log.info("echo_worker_running", task_id=str(task.id), title=task.title)
        return TaskResult(
            task_id=task.id,
            status=TaskStatus.COMPLETED,
            summary=f"Echo: {task.title}",
            output={"title": task.title, "description": task.description},
        )


class LLMWorker(BaseWorkerAgent):
    """
    Worker that uses an LLM provider to process tasks.

    The task description becomes the user prompt. The LLM response
    becomes the task output. Requires an LLM provider to be configured.

    Usage:
        from jackknife.blades.llm.litellm_provider import LiteLLMProvider
        worker = LLMWorker(provider=LiteLLMProvider("gpt-4o-mini"))
    """

    name: str = "llm_worker"
    description: str = "Processes tasks by calling an LLM provider"

    def __init__(self, provider: object, system_prompt: str | None = None) -> None:
        from jackknife.blades.llm.base import BaseLLMProvider
        from jackknife.blades.llm.models import LLMRequest

        self._provider: BaseLLMProvider = provider  # type: ignore[assignment]
        self._system_prompt = system_prompt
        self._LLMRequest = LLMRequest

    async def run(self, task: Task) -> TaskResult:
        from jackknife.blades.llm.models import LLMRequest

        messages = []
        if self._system_prompt:
            messages.append({"role": "system", "content": self._system_prompt})
        prompt = f"Task: {task.title}\n\n{task.description}"
        if task.context:
            import json

            prompt += f"\n\nContext:\n{json.dumps(task.context, indent=2)}"
        messages.append({"role": "user", "content": prompt})

        log.info("llm_worker_running", task_id=str(task.id), title=task.title)
        try:
            response = await self._provider.complete(LLMRequest(messages=messages))
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.COMPLETED,
                summary=response.content[:200],
                output={
                    "response": response.content,
                    "model": response.model,
                    "tokens": response.total_tokens,
                },
            )
        except Exception as exc:
            log.error("llm_worker_failed", task_id=str(task.id), error=str(exc))
            return TaskResult(
                task_id=task.id,
                status=TaskStatus.FAILED,
                error=str(exc),
            )
