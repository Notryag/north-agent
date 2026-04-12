from app.agent import create_chat_model


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
