from pathlib import Path

from langchain_core.messages import AIMessage

from north import AppClient, AppConfig
from north.tools.builtin.list_files import list_thread_file_uris
from north.tools.builtin.present_files import resolve_artifact_paths
from north.tools.builtin.read_file import read_text_file
from north.tools.builtin.write_report import write_report_file


def test_file_analysis_runs_from_upload_to_presented_artifact(tmp_path: Path) -> None:
    source = tmp_path / "brief.md"
    source.write_text("Revenue increased by 18 percent.", encoding="utf-8")
    thread_base_dir = tmp_path / "runtime-data"
    thread_id = "file-analysis-smoke"

    class ScriptedFileAnalysisAgent:
        def stream(self, state, *, config, context, stream_mode):
            del config, stream_mode
            assert context is not None
            base_dir = Path(context["thread_base_dir"])
            skills_dir = Path(context["skills_dir"])

            uris = list_thread_file_uris(thread_id=thread_id, base_dir=base_dir)
            assert uris == ["upload://brief.md"]
            content = read_text_file(
                uris[0],
                thread_id=thread_id,
                skills_dir=skills_dir,
                thread_base_dir=base_dir,
            )
            assert content == "Revenue increased by 18 percent."

            report_path = write_report_file(
                f"# Analysis\n\n{content}",
                thread_id=thread_id,
                base_dir=base_dir,
            )
            artifacts = resolve_artifact_paths(
                [report_path.name],
                thread_id=thread_id,
                base_dir=base_dir,
            )
            yield {
                "messages": [
                    *state["messages"],
                    AIMessage(content="Analysis complete.", id="analysis-complete"),
                ],
                "artifacts": artifacts,
            }

    client = AppClient(
        AppConfig(
            model_name="openai:gpt-4o-mini",
            skills_dir=tmp_path / "skills",
            thread_base_dir=thread_base_dir,
        )
    )
    client._agent = ScriptedFileAnalysisAgent()

    response = client.chat(
        "Analyze the uploaded brief and save a report.",
        thread_id=thread_id,
        files=[source],
    )

    assert response == "Analysis complete."
    assert response.artifacts == ("threads/file-analysis-smoke/outputs/report.md",)
    assert (thread_base_dir / response.artifacts[0]).read_text(encoding="utf-8") == (
        "# Analysis\n\nRevenue increased by 18 percent."
    )
