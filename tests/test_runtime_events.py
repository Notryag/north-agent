import asyncio
from types import SimpleNamespace
from uuid import uuid4

from langchain_core.messages import AIMessage

from north import RuntimeEvent, RuntimeJournal, invoke_agent_once


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
    assert events[1].content["tool_calls"][0]["name"] == "create_task"
    assert events[2].metadata["call_id"] == str(tool_run_id)
    assert events[2].content == {"title": "提交周报"}
    assert events[3].metadata["call_id"] == str(tool_run_id)


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
