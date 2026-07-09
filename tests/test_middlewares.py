from types import SimpleNamespace

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.types import Command

from north.agents.middlewares import (
    ClarificationMiddleware,
    LoopDetectionMiddleware,
    ToolErrorHandlingMiddleware,
    get_default_middlewares,
)


def test_default_middlewares_are_registered():
    middlewares = get_default_middlewares()

    assert [middleware.name for middleware in middlewares] == [
        "ToolErrorHandlingMiddleware",
        "LoopDetectionMiddleware",
        "ClarificationMiddleware",
    ]


def test_tool_error_middleware_converts_exceptions_to_tool_message():
    middleware = ToolErrorHandlingMiddleware()
    request = SimpleNamespace(tool_call={"id": "tool-1", "name": "web_fetch", "args": {"url": "https://example.com"}})

    result = middleware.wrap_tool_call(request, lambda _: (_ for _ in ()).throw(RuntimeError("network down")))

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert result.tool_call_id == "tool-1"
    assert "web_fetch" in result.content
    assert "network down" in result.content


def test_loop_detection_middleware_blocks_repeated_identical_calls():
    middleware = LoopDetectionMiddleware(max_same_call_count=2)
    repeated_call = {"name": "web_search", "args": {"query": "deerflow"}}
    request = SimpleNamespace(
        tool_call={"id": "tool-3", **repeated_call},
        state={
            "messages": [
                HumanMessage(content="Research DeerFlow"),
                AIMessage(content="", tool_calls=[{"id": "tool-1", **repeated_call}]),
                ToolMessage(content="first", tool_call_id="tool-1"),
                AIMessage(content="", tool_calls=[{"id": "tool-2", **repeated_call}]),
                ToolMessage(content="second", tool_call_id="tool-2"),
                AIMessage(content="", tool_calls=[{"id": "tool-3", **repeated_call}]),
            ]
        },
    )

    result = middleware.wrap_tool_call(request, lambda _: (_ for _ in ()).throw(AssertionError("handler should not run")))

    assert isinstance(result, ToolMessage)
    assert result.status == "error"
    assert "repeated tool loop" in result.content


def test_clarification_middleware_marks_pending_question():
    middleware = ClarificationMiddleware()
    request = SimpleNamespace(
        tool_call={"id": "tool-1", "name": "ask_clarification", "args": {"question": "Which company?"}},
        state={"thread_data": {"source": "user"}},
    )

    result = middleware.wrap_tool_call(
        request,
        lambda _: ToolMessage(
            content="Clarification needed: Which company?",
            tool_call_id="tool-1",
            name="ask_clarification",
        ),
    )

    assert isinstance(result, Command)
    assert result.update["thread_data"] == {
        "source": "user",
        "clarification": {"status": "pending", "question": "Which company?"},
    }
    assert len(result.update["messages"]) == 1


def test_clarification_middleware_clears_pending_question_on_user_reply():
    middleware = ClarificationMiddleware()

    update = middleware.before_model(
        {
            "thread_data": {
                "clarification": {"status": "pending", "question": "Which company?"},
                "source": "user",
            },
            "messages": [HumanMessage(content="OpenAI")],
        },
        runtime=None,
    )

    assert update == {"thread_data": {"source": "user"}}
