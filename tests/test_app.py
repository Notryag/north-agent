from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage

from app.client import AppClient
from app.config import AppConfig


def test_chat_returns_last_ai_message(monkeypatch):
    monkeypatch.setattr(
        "app.agent.create_chat_model",
        lambda name, thinking_enabled=False: FakeListChatModel(responses=["DeerFlow is an agent shell."]),
    )
    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))

    response = client.chat("Explain DeerFlow in one sentence.", thread_id="thread-1")

    assert response == "DeerFlow is an agent shell."


def test_stream_emits_message_and_values_events(monkeypatch):
    monkeypatch.setattr(
        "app.agent.create_chat_model",
        lambda name, thinking_enabled=False: FakeListChatModel(responses=["Minimal reply"]),
    )
    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))

    events = list(client.stream("hello", thread_id="thread-1"))

    assert [event.type for event in events] == ["values", "ai", "values", "end"]
    assert events[1].data == {"role": "ai", "content": "Minimal reply", "thread_id": "thread-1"}
    assert len(events[2].data["chunk"]["messages"]) == 2
    assert events[-1].data == {"thread_id": "thread-1"}


def test_stream_passes_thread_context_and_config():
    class StubAgent:
        def __init__(self):
            self.calls = []

        def stream(self, state, config=None, context=None, stream_mode=None):
            self.calls.append(
                {
                    "state": state,
                    "config": config,
                    "context": context,
                    "stream_mode": stream_mode,
                }
            )
            yield {"messages": [state["messages"][0], AIMessage(content="reply", id="ai-1")]}

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    stub_agent = StubAgent()
    client._agent = stub_agent

    events = list(client.stream("hello", thread_id="thread-ctx"))

    assert stub_agent.calls[0]["config"]["configurable"]["thread_id"] == "thread-ctx"
    assert stub_agent.calls[0]["context"] == {"thread_id": "thread-ctx"}
    assert stub_agent.calls[0]["stream_mode"] == "values"
    assert events[-1].type == "end"


def test_chat_returns_last_ai_event_content():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {"messages": [state["messages"][0], AIMessage(content="first", id="ai-1")]}
            yield {"messages": [state["messages"][0], AIMessage(content="last", id="ai-2")]}

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    assert client.chat("hello", thread_id="thread-1") == "last"


def test_stream_extracts_text_from_list_content():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {
                "messages": [
                    state["messages"][0],
                    AIMessage(content=[{"text": "part one"}, {"text": "part two"}], id="ai-1"),
                ]
            }

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    events = list(client.stream("hello", thread_id="thread-1"))

    assert events[1].type == "ai"
    assert events[1].data["content"] == "part one\npart two"
