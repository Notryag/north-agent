from langchain_core.language_models.fake_chat_models import FakeListChatModel

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

    assert [event.type for event in events] == ["values", "message", "values"]
    assert events[1].data == {"role": "ai", "content": "Minimal reply"}
    assert len(events[-1].data["messages"]) == 2
