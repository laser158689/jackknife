"""Tests for jackknife/blades/agents/worker.py — EchoWorker and LLMWorker."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from jackknife.blades.agents.models import Task, TaskResult, TaskStatus
from jackknife.blades.agents.worker import EchoWorker, LLMWorker
from jackknife.blades.llm.models import LLMResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_task(
    title: str = "Test Task",
    description: str = "Do the thing",
    context: dict | None = None,
) -> Task:
    return Task(title=title, description=description, context=context or {})


def _make_llm_response(content: str = "The answer", model: str = "gpt-4o-mini") -> LLMResponse:
    return LLMResponse(
        content=content,
        model=model,
        provider="openai",
        total_tokens=42,
    )


def _make_mock_provider(
    response: LLMResponse | None = None, raises: Exception | None = None
) -> MagicMock:
    provider = MagicMock()
    if raises is not None:
        provider.complete = AsyncMock(side_effect=raises)
    else:
        provider.complete = AsyncMock(return_value=response or _make_llm_response())
    return provider


# ---------------------------------------------------------------------------
# EchoWorker tests
# ---------------------------------------------------------------------------


class TestEchoWorker:
    def test_name_and_description(self):
        worker = EchoWorker()
        assert worker.name == "echo_worker"
        assert "echo" in worker.description.lower() or "output" in worker.description.lower()

    async def test_run_returns_completed_status(self):
        worker = EchoWorker()
        task = _make_task(title="Hello", description="World")
        result = await worker.run(task)
        assert result.status == TaskStatus.COMPLETED

    async def test_run_result_task_id_matches(self):
        worker = EchoWorker()
        task = _make_task()
        result = await worker.run(task)
        assert result.task_id == task.id

    async def test_run_summary_contains_title(self):
        worker = EchoWorker()
        task = _make_task(title="My Special Task")
        result = await worker.run(task)
        assert "My Special Task" in result.summary

    async def test_run_output_has_title_and_description(self):
        worker = EchoWorker()
        task = _make_task(title="Alpha", description="Beta description")
        result = await worker.run(task)
        assert result.output["title"] == "Alpha"
        assert result.output["description"] == "Beta description"

    async def test_run_returns_task_result_instance(self):
        worker = EchoWorker()
        task = _make_task()
        result = await worker.run(task)
        assert isinstance(result, TaskResult)

    def test_can_handle_returns_true_by_default(self):
        worker = EchoWorker()
        task = _make_task()
        assert worker.can_handle(task) is True

    async def test_run_empty_description(self):
        worker = EchoWorker()
        task = _make_task(title="Empty", description="")
        result = await worker.run(task)
        assert result.status == TaskStatus.COMPLETED
        assert result.output["description"] == ""

    async def test_multiple_runs_independent(self):
        worker = EchoWorker()
        task_a = _make_task(title="A", description="desc A")
        task_b = _make_task(title="B", description="desc B")
        result_a = await worker.run(task_a)
        result_b = await worker.run(task_b)
        assert result_a.task_id != result_b.task_id
        assert "A" in result_a.summary
        assert "B" in result_b.summary


# ---------------------------------------------------------------------------
# LLMWorker tests
# ---------------------------------------------------------------------------


class TestLLMWorkerInit:
    def test_stores_provider(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        assert worker._provider is provider

    def test_system_prompt_defaults_to_none(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        assert worker._system_prompt is None

    def test_custom_system_prompt_stored(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider, system_prompt="You are helpful.")
        assert worker._system_prompt == "You are helpful."

    def test_name_and_description(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        assert worker.name == "llm_worker"
        assert "llm" in worker.description.lower() or "language" in worker.description.lower()


class TestLLMWorkerRun:
    async def test_successful_run_returns_completed(self):
        response = _make_llm_response(content="Great answer", model="gpt-4o")
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task(title="Summarise", description="Please summarise this document.")
        result = await worker.run(task)
        assert result.status == TaskStatus.COMPLETED

    async def test_successful_run_task_id_matches(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.task_id == task.id

    async def test_successful_run_output_contains_response(self):
        response = _make_llm_response(content="42 is the answer")
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.output["response"] == "42 is the answer"

    async def test_successful_run_output_contains_model(self):
        response = _make_llm_response(model="gpt-4o-mini")
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.output["model"] == "gpt-4o-mini"

    async def test_successful_run_output_contains_tokens(self):
        response = _make_llm_response()
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.output["tokens"] == response.total_tokens

    async def test_summary_truncated_to_200_chars(self):
        long_content = "X" * 300
        response = _make_llm_response(content=long_content)
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.summary == long_content[:200]
        assert len(result.summary) == 200

    async def test_summary_short_content_not_truncated(self):
        short_content = "Short reply"
        response = _make_llm_response(content=short_content)
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.summary == short_content

    async def test_provider_complete_called_once(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task()
        await worker.run(task)
        provider.complete.assert_called_once()

    async def test_prompt_includes_task_title_and_description(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task(title="My Title", description="My Description")
        await worker.run(task)
        call_args = provider.complete.call_args
        llm_request = call_args.args[0]
        user_message = next(m for m in llm_request.messages if m["role"] == "user")
        assert "My Title" in user_message["content"]
        assert "My Description" in user_message["content"]

    async def test_no_system_prompt_means_single_message(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider, system_prompt=None)
        task = _make_task()
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        roles = [m["role"] for m in llm_request.messages]
        assert "system" not in roles
        assert roles == ["user"]

    async def test_system_prompt_added_as_first_message(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider, system_prompt="Be concise.")
        task = _make_task()
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        assert llm_request.messages[0]["role"] == "system"
        assert llm_request.messages[0]["content"] == "Be concise."

    async def test_system_prompt_followed_by_user_message(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider, system_prompt="Help.")
        task = _make_task()
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        assert llm_request.messages[1]["role"] == "user"

    async def test_context_dict_included_in_prompt(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task(context={"key": "value", "number": 7})
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        user_message = next(m for m in llm_request.messages if m["role"] == "user")
        assert "key" in user_message["content"]
        assert "value" in user_message["content"]

    async def test_empty_context_not_included_in_prompt(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task(context={})
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        user_message = next(m for m in llm_request.messages if m["role"] == "user")
        assert "Context:" not in user_message["content"]

    async def test_exception_returns_failed_status(self):
        provider = _make_mock_provider(raises=RuntimeError("LLM timed out"))
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.status == TaskStatus.FAILED

    async def test_exception_error_message_captured(self):
        provider = _make_mock_provider(raises=ValueError("Bad request"))
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.error == "Bad request"

    async def test_exception_result_task_id_matches(self):
        provider = _make_mock_provider(raises=Exception("boom"))
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert result.task_id == task.id

    async def test_exception_result_is_task_result_instance(self):
        provider = _make_mock_provider(raises=Exception("fail"))
        worker = LLMWorker(provider=provider)
        task = _make_task()
        result = await worker.run(task)
        assert isinstance(result, TaskResult)

    def test_can_handle_returns_true(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        task = _make_task()
        assert worker.can_handle(task) is True

    async def test_context_json_serialised_in_prompt(self):
        import json

        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider)
        ctx = {"nested": {"a": 1}, "list": [1, 2, 3]}
        task = _make_task(context=ctx)
        await worker.run(task)
        llm_request = provider.complete.call_args.args[0]
        user_message = next(m for m in llm_request.messages if m["role"] == "user")
        expected_json = json.dumps(ctx, indent=2)
        assert expected_json in user_message["content"]

    async def test_run_with_both_system_prompt_and_context(self):
        provider = _make_mock_provider()
        worker = LLMWorker(provider=provider, system_prompt="You are an expert.")
        task = _make_task(title="Analyse", description="...", context={"data": "some data"})
        result = await worker.run(task)
        assert result.status == TaskStatus.COMPLETED
        llm_request = provider.complete.call_args.args[0]
        assert llm_request.messages[0]["role"] == "system"
        user_msg = llm_request.messages[1]["content"]
        assert "data" in user_msg

    async def test_unique_task_ids_across_runs(self):
        response = _make_llm_response()
        provider = _make_mock_provider(response=response)
        worker = LLMWorker(provider=provider)
        task1 = _make_task(title="Task 1")
        task2 = _make_task(title="Task 2")
        result1 = await worker.run(task1)
        result2 = await worker.run(task2)
        assert result1.task_id != result2.task_id
