from app.client import ChatResponse, StreamEvent
from app.cli import format_artifacts, format_stream_event, main
from app.config import AppConfig


def test_format_artifacts_handles_empty_and_present_artifacts():
    assert format_artifacts(()) == ""
    assert format_artifacts(("output://report.md",)) == "Artifacts:\n- output://report.md"


def test_format_stream_event_summarizes_tool_values_and_errors():
    assert (
        format_stream_event(
            StreamEvent(
                type="tool",
                data={
                    "name": "present_files",
                    "status": "success",
                    "content": "Files:\n- output://report.md",
                },
            )
        )
        == "[tool:present_files] success\nFiles:\n- output://report.md"
    )
    assert (
        format_stream_event(StreamEvent(type="values", data={"artifacts": ("output://report.md",)}))
        == "[values] artifacts=output://report.md"
    )
    assert (
        format_stream_event(StreamEvent(type="error", data={"error_type": "RuntimeError", "message": "boom"}))
        == "[error:RuntimeError] boom"
    )
    assert format_stream_event(StreamEvent(type="ai", data={"content": "hello"})) == ""


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


def test_cli_stream_show_events_prints_tool_and_values_events(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, config):
            self.config = config

        def stream(self, message, *, thread_id=None, skills=None, files=None):
            yield StreamEvent(
                type="tool",
                data={
                    "name": "present_files",
                    "status": "success",
                    "content": "Files:\n- output://report.md",
                    "artifacts": ("output://report.md",),
                },
            )
            yield StreamEvent(type="values", data={"artifacts": ("output://report.md",)})
            yield StreamEvent(type="ai", data={"content": "done", "artifacts": ("output://report.md",)})
            yield StreamEvent(type="end", data={"artifacts": ("output://report.md",)})

    monkeypatch.setattr("app.cli.AppClient", FakeClient)
    monkeypatch.setattr(
        "app.cli.AppConfig.from_env",
        classmethod(lambda cls: AppConfig(model_name="openai:gpt-4o-mini")),
    )
    monkeypatch.setattr("app.cli.AppConfig.validate", lambda self: None)
    monkeypatch.setattr("sys.argv", ["deerflow-lite", "--stream", "--show-events", "hello"])

    assert main() == 0

    assert capsys.readouterr().out == (
        "[tool:present_files] success\n"
        "Files:\n"
        "- output://report.md\n"
        "[values] artifacts=output://report.md\n"
        "done\n"
        "Artifacts:\n"
        "- output://report.md\n"
    )
