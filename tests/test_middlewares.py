from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from app.config import AppConfig
from app.middlewares import ClarificationMiddleware, LoopDetectionMiddleware, ToolErrorHandlingMiddleware
from app.runtime import get_middlewares


def test_runtime_returns_three_middlewares():
    middlewares = get_middlewares(AppConfig(model_name="openai:gpt-4o-mini"))

    assert [type(m).__name__ for m in middlewares] == [
        "ToolErrorHandlingMiddleware",
        "LoopDetectionMiddleware",
        "ClarificationMiddleware",
    ]


def test_clarification_middleware_short_circuits_short_input():
    middleware = ClarificationMiddleware()

    class Request:
        state = {"messages": [HumanMessage(content="hi")]}

    result = middleware.wrap_model_call(Request(), lambda _request: AIMessage(content="should not happen"))

    assert isinstance(result, AIMessage)
    assert "more detail" in result.content


def test_tool_error_middleware_turns_exceptions_into_ai_message():
    middleware = ToolErrorHandlingMiddleware()

    class Request:
        state = {"messages": [HumanMessage(content="hello")]}

    result = middleware.wrap_model_call(Request(), lambda _request: (_ for _ in ()).throw(RuntimeError("boom")))

    assert isinstance(result, AIMessage)
    assert "boom" in result.content


def test_loop_detection_middleware_replaces_repeated_output():
    middleware = LoopDetectionMiddleware()

    class Request:
        state = {"messages": [HumanMessage(content="hello"), AIMessage(content="repeat")]}

    class Response:
        result = [AIMessage(content="repeat")]

    result = middleware.wrap_model_call(Request(), lambda _request: Response())

    assert isinstance(result, AIMessage)
    assert "Loop detected" in result.content
