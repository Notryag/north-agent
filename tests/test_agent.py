from app.agent import build_agent, create_chat_model
from app.config import AppConfig


def test_create_chat_model_defaults_plain_names_to_openai_provider(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("app.agent.init_chat_model", fake_init_chat_model)

    create_chat_model("qwen3.6-plus")

    assert captured == {"model": "qwen3.6-plus", "model_provider": "openai"}


def test_create_chat_model_preserves_explicit_provider(monkeypatch):
    captured = {}

    def fake_init_chat_model(**kwargs):
        captured.update(kwargs)
        return object()

    monkeypatch.setattr("app.agent.init_chat_model", fake_init_chat_model)

    create_chat_model("openai:gpt-4o-mini")

    assert captured == {"model": "gpt-4o-mini", "model_provider": "openai"}


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

    monkeypatch.setattr("app.agent.create_chat_model", fake_create_chat_model)
    monkeypatch.setattr("app.agent._supports_tool_binding", lambda model: True)
    monkeypatch.setattr("app.agent.create_agent", fake_create_agent)

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
