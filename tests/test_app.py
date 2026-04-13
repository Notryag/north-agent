from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, ToolMessage

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
    assert response.thread_id == "thread-1"
    assert response.artifacts == ()


def test_stream_emits_message_and_values_events(monkeypatch):
    monkeypatch.setattr(
        "app.agent.create_chat_model",
        lambda name, thinking_enabled=False: FakeListChatModel(responses=["Minimal reply"]),
    )
    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))

    events = list(client.stream("hello", thread_id="thread-1"))

    assert [event.type for event in events] == ["values", "ai", "values", "end"]
    assert events[1].data == {
        "role": "ai",
        "content": "Minimal reply",
        "thread_id": "thread-1",
        "artifacts": (),
    }
    assert len(events[2].data["chunk"]["messages"]) == 2
    assert events[-1].data == {"thread_id": "thread-1", "artifacts": ()}


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
    assert stub_agent.calls[0]["context"] == {
        "thread_id": "thread-ctx",
        "skills_dir": str(client.config.skills_dir.resolve()),
    }
    assert stub_agent.calls[0]["stream_mode"] == "values"
    assert events[-1].type == "end"


def test_chat_returns_last_ai_event_content():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {"messages": [state["messages"][0], AIMessage(content="first", id="ai-1")]}
            yield {"messages": [state["messages"][0], AIMessage(content="last", id="ai-2")]}

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    response = client.chat("hello", thread_id="thread-1")

    assert response == "last"
    assert response.artifacts == ()


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

    assert [event.type for event in events] == ["ai", "values", "end"]
    assert events[0].data["content"] == "part one\npart two"


def test_stream_emits_tool_events_with_artifacts():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {
                "messages": [
                    state["messages"][0],
                    ToolMessage(
                        content="Files:\n- .deerflow/threads/thread-1/outputs/report.md",
                        name="present_files",
                        tool_call_id="tool-1",
                    ),
                ],
                "artifacts": [".deerflow/threads/thread-1/outputs/report.md"],
            }
            yield {
                "messages": [state["messages"][0], AIMessage(content="done", id="ai-1")],
                "artifacts": [".deerflow/threads/thread-1/outputs/report.md"],
            }

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    events = list(client.stream("hello", thread_id="thread-1"))

    assert [event.type for event in events] == ["tool", "values", "ai", "values", "end"]
    assert events[0].data["name"] == "present_files"
    assert events[0].data["artifacts"] == (".deerflow/threads/thread-1/outputs/report.md",)
    assert events[-1].data["artifacts"] == (".deerflow/threads/thread-1/outputs/report.md",)


def test_chat_carries_artifacts_from_stream():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {
                "messages": [
                    state["messages"][0],
                    ToolMessage(
                        content="Files:\n- .deerflow/threads/thread-1/outputs/report.md",
                        name="present_files",
                        tool_call_id="tool-1",
                    ),
                ],
                "artifacts": [".deerflow/threads/thread-1/outputs/report.md"],
            }
            yield {
                "messages": [state["messages"][0], AIMessage(content="final answer", id="ai-1")],
                "artifacts": [".deerflow/threads/thread-1/outputs/report.md"],
            }

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    response = client.chat("hello", thread_id="thread-1")

    assert response == "final answer"
    assert response.artifacts == (".deerflow/threads/thread-1/outputs/report.md",)


def test_stream_emits_error_event_before_reraising():
    class StubAgent:
        def stream(self, state, config=None, context=None, stream_mode=None):
            raise RuntimeError("boom")
            yield state

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))
    client._agent = StubAgent()

    iterator = client.stream("hello", thread_id="thread-1")
    event = next(iterator)

    assert event.type == "error"
    assert event.data == {
        "thread_id": "thread-1",
        "message": "boom",
        "error_type": "RuntimeError",
    }

    try:
        next(iterator)
        assert False, "Expected RuntimeError to be re-raised"
    except RuntimeError as exc:
        assert str(exc) == "boom"


def test_client_builds_distinct_agents_for_skill_sets(monkeypatch):
    calls = []

    class StubAgent:
        def __init__(self, label):
            self.label = label

        def stream(self, state, config=None, context=None, stream_mode=None):
            yield {"messages": [state["messages"][0], AIMessage(content=self.label, id=f"ai-{self.label}")]}

    def fake_build_agent(config, *, checkpointer=None, skills=None):
        calls.append(tuple(skills or ()))
        return StubAgent(label=",".join(skills or ()) or "default")

    monkeypatch.setattr("app.client.build_agent", fake_build_agent)

    client = AppClient(AppConfig(model_name="openai:gpt-4o-mini"))

    assert client.chat("hello") == "default"
    assert client.chat("hello", skills=["research"]) == "research"
    assert client.chat("hello", skills=["research"]) == "research"
    assert client.chat("hello", skills=["writer"]) == "writer"
    assert calls == [(), ("research",), ("writer",)]
