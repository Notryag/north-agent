import asyncio
from types import SimpleNamespace
from uuid import uuid4

from langchain_core.messages import AIMessage

from north import (
    RuntimeEvent,
    RuntimeJournal,
    RuntimeStreamEvent,
    RuntimeUsageAccumulator,
    invoke_agent_once,
    normalize_token_usage,
    stream_agent_once,
)


def test_runtime_journal_emits_correlated_model_and_tool_events() -> None:
    asyncio.run(_assert_runtime_journal_events())


async def _assert_runtime_journal_events() -> None:
    events: list[RuntimeEvent] = []

    async def sink(event: RuntimeEvent) -> None:
        events.append(event)

    journal = RuntimeJournal(sink)
    model_run_id = uuid4()
    tool_run_id = uuid4()
    await journal.on_chat_model_start({}, [[]], run_id=model_run_id, tags=["lead_agent"])
    await journal.on_llm_end(
        SimpleNamespace(
            generations=[
                [
                    SimpleNamespace(
                        message=AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "id": "call-1",
                                    "name": "create_task",
                                    "args": {"title": "提交周报"},
                                }
                            ],
                            usage_metadata={
                                "input_tokens": 10,
                                "output_tokens": 4,
                                "total_tokens": 14,
                            },
                        )
                    )
                ]
            ]
        ),
        run_id=model_run_id,
        tags=["lead_agent"],
    )
    await journal.on_tool_start(
        {"name": "create_task"},
        "",
        run_id=tool_run_id,
        inputs={"title": "提交周报"},
    )
    await journal.on_tool_end(
        {"task_id": "task-1"},
        run_id=tool_run_id,
    )

    assert [event.event_type for event in events] == [
        "model.started",
        "model.completed",
        "tool.started",
        "tool.completed",
    ]
    assert events[0].metadata["caller"] == "lead_agent"
    assert events[1].metadata["usage"]["total_tokens"] == 14
    assert events[1].metadata["call_index"] == 1
    assert events[1].content["tool_calls"][0]["name"] == "create_task"
    assert events[2].metadata["call_id"] == str(tool_run_id)
    assert events[2].content == {"title": "提交周报"}
    assert events[3].metadata["call_id"] == str(tool_run_id)
    assert events[3].metadata["tool_name"] == "create_task"


def test_normalizes_provider_usage_aliases_and_derives_total() -> None:
    usage = normalize_token_usage(
        {"token_usage": {"prompt_tokens": 12, "completion_tokens": 3}}
    )

    assert usage is not None
    assert usage.as_dict() == {
        "input_tokens": 12,
        "output_tokens": 3,
        "total_tokens": 15,
    }


def test_runtime_usage_accumulator_sums_each_model_call_once() -> None:
    asyncio.run(_assert_runtime_usage_accumulator())


async def _assert_runtime_usage_accumulator() -> None:
    accumulator = RuntimeUsageAccumulator()
    first = RuntimeEvent(
        "model.completed",
        "model",
        metadata={
            "call_id": "call-1",
            "usage": {"input_tokens": 10, "output_tokens": 2, "total_tokens": 12},
        },
    )
    await accumulator(first)
    await accumulator(first)
    await accumulator(
        RuntimeEvent(
            "model.completed",
            "model",
            metadata={
                "call_id": "call-2",
                "usage": {"prompt_tokens": 7, "completion_tokens": 1},
            },
        )
    )

    assert accumulator.total is not None
    assert accumulator.total.as_dict() == {
        "input_tokens": 17,
        "output_tokens": 3,
        "total_tokens": 20,
    }
    assert [call["call_id"] for call in accumulator.calls] == ["call-1", "call-2"]


def test_invoke_agent_once_merges_runtime_journal_with_existing_callbacks() -> None:
    asyncio.run(_assert_invoke_agent_once_merges_callbacks())


async def _assert_invoke_agent_once_merges_callbacks() -> None:
    existing_callback = object()
    captured = {}

    class StubAgent:
        async def ainvoke(self, graph_input, *, config=None, context=None):
            captured.update(graph_input=graph_input, config=config, context=context)
            return {"ok": True}

    async def sink(event: RuntimeEvent) -> None:
        del event

    result = await invoke_agent_once(
        agent_factory=StubAgent,
        graph_input={"messages": []},
        config={"callbacks": [existing_callback], "configurable": {"thread_id": "thread-1"}},
        context={"run_id": "run-1"},
        event_sink=sink,
    )

    assert result == {"ok": True}
    assert captured["config"]["callbacks"][0] is existing_callback
    assert isinstance(captured["config"]["callbacks"][1], RuntimeJournal)
    assert captured["config"]["configurable"] == {"thread_id": "thread-1"}
    assert captured["context"] == {"run_id": "run-1"}


def test_stream_agent_once_normalizes_messages_and_returns_latest_values() -> None:
    asyncio.run(_assert_stream_agent_once_normalizes_chunks())


async def _assert_stream_agent_once_normalizes_chunks() -> None:
    captured = {}
    events: list[RuntimeStreamEvent] = []

    class StubAgent:
        async def astream(
            self,
            graph_input,
            *,
            config=None,
            context=None,
            stream_mode=None,
        ):
            captured.update(
                graph_input=graph_input,
                config=config,
                context=context,
                stream_mode=stream_mode,
            )
            yield ("messages", (AIMessage(content="好"), {"langgraph_node": "model"}))
            yield ("values", {"messages": [AIMessage(content="好了")]})

    async def stream_sink(event: RuntimeStreamEvent) -> None:
        events.append(event)

    result = await stream_agent_once(
        agent_factory=StubAgent,
        graph_input={"messages": []},
        config={"configurable": {"thread_id": "thread-1"}},
        context={"run_id": "run-1"},
        stream_sink=stream_sink,
    )

    assert captured["stream_mode"] == ["values", "messages"]
    assert captured["context"] == {"run_id": "run-1"}
    assert [event.mode for event in events] == ["messages", "values"]
    assert events[0].data[0]["content"] == "好"
    assert result["messages"][0]["content"] == "好了"


def test_stream_agent_once_falls_back_to_ainvoke() -> None:
    asyncio.run(_assert_stream_agent_once_fallback())


async def _assert_stream_agent_once_fallback() -> None:
    events: list[RuntimeStreamEvent] = []

    class StubAgent:
        async def ainvoke(self, graph_input, *, config=None, context=None):
            del graph_input, config, context
            return {"answer": "done"}

    async def stream_sink(event: RuntimeStreamEvent) -> None:
        events.append(event)

    result = await stream_agent_once(
        agent_factory=StubAgent,
        graph_input={"messages": []},
        stream_sink=stream_sink,
    )

    assert result == {"answer": "done"}
    assert events == [RuntimeStreamEvent(mode="values", data={"answer": "done"})]
