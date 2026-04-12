import pytest

from app.config import AppConfig


def test_validate_requires_langsmith_api_key_when_tracing_enabled(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="LANGSMITH_API_KEY is not set"):
        AppConfig(model_name="openai:gpt-4o-mini").validate()


def test_validate_allows_langsmith_when_api_key_is_present(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "ls-key")

    AppConfig(model_name="openai:gpt-4o-mini").validate()
