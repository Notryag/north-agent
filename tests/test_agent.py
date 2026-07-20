import pytest

from north.agent import build_agent, create_chat_model
from north.config import AppConfig


def test_create_chat_model_defaults_plain_names_to_openai_provider(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("north.agent.init_chat_model", fake_init_chat_model)

    create_chat_model("qwen3.6-plus")

    assert captured == {"model": "qwen3.6-plus", "model_provider": "openai"}


def test_create_chat_model_preserves_explicit_provider(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("north.agent.init_chat_model", fake_init_chat_model)

    create_chat_model("openai:gpt-4o-mini")

    assert captured == {"model": "gpt-4o-mini", "model_provider": "openai"}


def test_create_chat_model_forwards_host_headers(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("north.agent.init_chat_model", fake_init_chat_model)

    create_chat_model(
        "openai:gpt-4o-mini",
        default_headers={"Northgate-Metadata": '{"run_id":"run-1"}'},
    )

    assert captured == {
        "model": "gpt-4o-mini",
        "model_provider": "openai",
        "default_headers": {"Northgate-Metadata": '{"run_id":"run-1"}'},
    }


def test_create_chat_model_forwards_host_connection_options(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("north.agent.init_chat_model", fake_init_chat_model)

    create_chat_model(
        "openai:gpt-4o-mini",
        model_options={"base_url": "http://northgate:8080/v1", "api_key": "application-key"},
    )

    assert captured == {
        "model": "gpt-4o-mini",
        "model_provider": "openai",
        "base_url": "http://northgate:8080/v1",
        "api_key": "application-key",
    }


def test_create_chat_model_rejects_reserved_connection_options() -> None:
    with pytest.raises(ValueError, match="model_provider"):
        create_chat_model(
            "openai:gpt-4o-mini",
            model_options={"model_provider": "anthropic"},
        )


def test_build_agent_injects_skill_catalog_not_skill_body(monkeypatch, tmp_path):
    skill_dir = tmp_path / "skills" / "research"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: research\ndescription: Web research workflow\n---\nDetailed body content.\n",
        encoding="utf-8",
    )

    captured = {}

    class StubModel:
        pass

    def fake_create_chat_model(name, thinking_enabled=False):
        _ = name, thinking_enabled
        return StubModel()

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("north.agent.create_chat_model", fake_create_chat_model)
    monkeypatch.setattr("north.agent._supports_tool_binding", lambda model: True)
    monkeypatch.setattr("north.agent.create_agent", fake_create_agent)

    build_agent(
        AppConfig(
            model_name="openai:gpt-4o-mini",
            system_prompt="Base prompt.",
            skills_dir=tmp_path / "skills",
        )
    )

    assert "<available_skills>" in captured["system_prompt"]
    assert "<location>skill://research/SKILL.md</location>" in captured["system_prompt"]
    assert "Detailed body content." not in captured["system_prompt"]


def test_build_agent_combines_token_and_message_summarization_triggers(monkeypatch):
    captured = {}

    class StubModel:
        def with_config(self, **kwargs):
            captured["summary_model_config"] = kwargs
            return self

    class StubSummarizationMiddleware:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr("north.agent.create_chat_model", lambda *args, **kwargs: StubModel())
    monkeypatch.setattr("north.agent._supports_tool_binding", lambda model: True)
    monkeypatch.setattr("north.agent.NorthSummarizationMiddleware", StubSummarizationMiddleware)
    monkeypatch.setattr("north.agent.create_agent", lambda **kwargs: object())

    build_agent(
        AppConfig(
            model_name="openai:gpt-test",
            summarization_enabled=True,
            summarization_trigger_tokens=1200,
            summarization_trigger_messages=40,
            summarization_keep_messages=12,
        ),
        tools=[],
    )

    assert captured["trigger"] == [("tokens", 1200), ("messages", 40)]
    assert captured["keep"] == ("messages", 12)
    assert captured["summary_model_config"] == {"tags": ["middleware:summarization"]}


def test_build_agent_appends_host_middlewares_after_runtime_defaults(monkeypatch):
    captured = {}
    runtime_middleware = object()
    host_middleware = object()

    class StubModel:
        pass

    monkeypatch.setattr("north.agent.create_chat_model", lambda *args, **kwargs: StubModel())
    monkeypatch.setattr("north.agent._supports_tool_binding", lambda model: True)
    monkeypatch.setattr(
        "north.agent.resolve_middlewares", lambda config: [runtime_middleware]
    )
    monkeypatch.setattr(
        "north.agent.create_agent", lambda **kwargs: captured.update(kwargs) or object()
    )

    build_agent(
        AppConfig(model_name="openai:gpt-test"),
        tools=[],
        additional_middlewares=[host_middleware],
    )

    assert captured["middleware"] == [runtime_middleware, host_middleware]
