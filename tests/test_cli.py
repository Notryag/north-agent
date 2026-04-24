from app.client import ChatResponse, StreamEvent
from app.cli import format_artifacts, main
from app.config import AppConfig


def test_format_artifacts_handles_empty_and_present_artifacts():
    assert format_artifacts(()) == ""
    assert format_artifacts(("output://report.md",)) == "Artifacts:\n- output://report.md"


def test_cli_prints_chat_artifacts(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, config):
            self.config = config

        def chat(self, message, *, thread_id=None, skills=None, files=None):
            assert message == "hello"
            assert thread_id == "thread-1"
            assert skills == ["writer"]
            assert files == ["notes.md"]
            return ChatResponse(
                "done",
                thread_id="thread-1",
                artifacts=("output://report.md",),
            )

    monkeypatch.setattr("app.cli.AppClient", FakeClient)
    monkeypatch.setattr(
        "app.cli.AppConfig.from_env",
        classmethod(lambda cls: AppConfig(model_name="openai:gpt-4o-mini")),
    )
    monkeypatch.setattr("app.cli.AppConfig.validate", lambda self: None)
    monkeypatch.setattr(
        "sys.argv",
        ["deerflow-lite", "--thread-id", "thread-1", "--skill", "writer", "--file", "notes.md", "hello"],
    )

    assert main() == 0

    assert capsys.readouterr().out == "done\nArtifacts:\n- output://report.md\n"


def test_cli_stream_prints_final_artifacts(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, config):
            self.config = config

        def stream(self, message, *, thread_id=None, skills=None, files=None):
            yield StreamEvent(type="ai", data={"content": "chunk", "artifacts": ()})
            yield StreamEvent(type="end", data={"artifacts": ("output://report.md",)})

    monkeypatch.setattr("app.cli.AppClient", FakeClient)
    monkeypatch.setattr(
        "app.cli.AppConfig.from_env",
        classmethod(lambda cls: AppConfig(model_name="openai:gpt-4o-mini")),
    )
    monkeypatch.setattr("app.cli.AppConfig.validate", lambda self: None)
    monkeypatch.setattr("sys.argv", ["deerflow-lite", "--stream", "hello"])

    assert main() == 0

    assert capsys.readouterr().out == "chunk\nArtifacts:\n- output://report.md\n"
