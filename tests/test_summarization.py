import asyncio
from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage

from north import CompactionEvent, NorthSummarizationMiddleware


class SummaryModel:
    async def ainvoke(self, prompt, config=None):
        del prompt, config
        return AIMessage(content="用户正在安排发布会议，尚未确定参会人。")


def _runtime(run_id: str):
    return SimpleNamespace(context={"run_id": run_id})


def _middleware(*, hooks=None, **overrides) -> NorthSummarizationMiddleware:
    options = {
        "normal_trigger_tokens": 5,
        "emergency_trigger_tokens": 12,
        "message_ceiling": 100,
        "target_tokens": 2,
        "min_growth_tokens": 3,
        "max_emergency_compactions": 2,
        "token_counter": lambda messages: len(list(messages)),
        "compaction_hooks": hooks,
    }
    options.update(overrides)
    return NorthSummarizationMiddleware(model=SummaryModel(), **options)


def _materialize_update(update: dict) -> dict:
    return {
        **{key: value for key, value in update.items() if key != "messages"},
        "messages": [
            message for message in update["messages"] if not isinstance(message, RemoveMessage)
        ],
    }


def test_async_normal_compaction_preserves_recent_messages_and_calls_hook() -> None:
    events: list[CompactionEvent] = []

    async def record(event: CompactionEvent) -> None:
        events.append(event)

    middleware = _middleware(hooks=[record])
    messages = [
        HumanMessage(content="安排发布会"),
        AIMessage(content="什么时候？"),
        HumanMessage(content="明天下午"),
        AIMessage(content="参会人呢？"),
        HumanMessage(content="还没确定"),
    ]

    update = asyncio.run(
        middleware.abefore_model({"messages": messages}, _runtime("run-1"))
    )

    assert update is not None
    assert update["summary_text"] == "用户正在安排发布会议，尚未确定参会人。"
    assert isinstance(update["messages"][0], RemoveMessage)
    assert update["messages"][-2:] == messages[-2:]
    assert update["compaction_run_id"] == "run-1"
    assert update["normal_compaction_done"] is True
    assert update["emergency_compaction_count"] == 0
    assert len(events) == 1
    assert events[0].kind == "normal"
    assert events[0].run_id == "run-1"
    assert events[0].summarized_messages == tuple(messages[:3])
    assert events[0].preserved_messages == tuple(messages[-2:])


def test_same_run_never_performs_normal_compaction_twice() -> None:
    middleware = _middleware(emergency_trigger_tokens=20)
    messages = [HumanMessage(content=str(index)) for index in range(5)]
    first = asyncio.run(
        middleware.abefore_model({"messages": messages}, _runtime("run-1"))
    )
    assert first is not None
    state = _materialize_update(first)
    state["messages"].extend(HumanMessage(content=str(index)) for index in range(5, 10))

    second = asyncio.run(middleware.abefore_model(state, _runtime("run-1")))

    assert second is None


def test_emergency_compaction_requires_minimum_growth_and_is_bounded() -> None:
    middleware = _middleware(
        normal_trigger_tokens=5,
        emergency_trigger_tokens=6,
        context_token_overhead=4,
        min_growth_tokens=3,
    )
    first_state = {"messages": [HumanMessage(content=str(index)) for index in range(3)]}
    first = asyncio.run(
        middleware.abefore_model(first_state, _runtime("run-emergency"))
    )
    assert first is not None
    assert first["normal_compaction_done"] is False
    assert first["emergency_compaction_count"] == 1

    state = _materialize_update(first)
    state["messages"].append(HumanMessage(content="insufficient growth"))
    blocked = asyncio.run(
        middleware.abefore_model(state, _runtime("run-emergency"))
    )
    assert blocked is None

    state["messages"].extend(
        [HumanMessage(content="growth-2"), HumanMessage(content="growth-3")]
    )
    second = asyncio.run(
        middleware.abefore_model(state, _runtime("run-emergency"))
    )
    assert second is not None
    assert second["emergency_compaction_count"] == 2

    bounded_state = _materialize_update(second)
    bounded_state["messages"].extend(
        HumanMessage(content=str(index)) for index in range(10)
    )
    bounded = asyncio.run(
        middleware.abefore_model(bounded_state, _runtime("run-emergency"))
    )
    assert bounded is None


def test_new_run_resets_compaction_counters() -> None:
    middleware = _middleware()
    state = {
        "messages": [HumanMessage(content=str(index)) for index in range(5)],
        "compaction_run_id": "run-old",
        "normal_compaction_done": True,
        "emergency_compaction_count": 2,
        "compaction_retained_tokens": 2,
    }

    update = asyncio.run(middleware.abefore_model(state, _runtime("run-new")))

    assert update is not None
    assert update["compaction_run_id"] == "run-new"
    assert update["normal_compaction_done"] is True
    assert update["emergency_compaction_count"] == 0


def test_token_cutoff_keeps_ai_tool_call_batch_atomic() -> None:
    middleware = _middleware(normal_trigger_tokens=6, target_tokens=4)
    ai = AIMessage(
        content="",
        tool_calls=[
            {"id": "call-1", "name": "first", "args": {}},
            {"id": "call-2", "name": "second", "args": {}},
        ],
    )
    first_tool = ToolMessage(content="{}", tool_call_id="call-1", name="first")
    second_tool = ToolMessage(content="{}", tool_call_id="call-2", name="second")
    messages = [
        HumanMessage(content="old"),
        ai,
        first_tool,
        second_tool,
        HumanMessage(content="continue"),
        AIMessage(content="working"),
    ]

    update = asyncio.run(
        middleware.abefore_model({"messages": messages}, _runtime("run-tools"))
    )

    assert update is not None
    preserved = update["messages"][2:]
    assert preserved == [ai, first_tool, second_tool, *messages[-2:]]


def test_first_model_call_without_compaction_records_run_identity() -> None:
    middleware = _middleware()

    update = asyncio.run(
        middleware.abefore_model(
            {"messages": [HumanMessage(content="short")]},
            _runtime("run-short"),
        )
    )

    assert update == {
        "compaction_run_id": "run-short",
        "normal_compaction_done": False,
        "emergency_compaction_count": 0,
        "compaction_retained_tokens": None,
    }
