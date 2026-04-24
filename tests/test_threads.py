from pathlib import Path

from app.threads.paths import ThreadPaths
from app.threads.uploads import store_upload_file, store_upload_files


def test_thread_paths_resolve_expected_directories(tmp_path: Path):
    paths = ThreadPaths(thread_id="thread-1", base_dir=tmp_path)

    assert paths.thread_dir == tmp_path / "threads" / "thread-1"
    assert paths.workspace_dir == tmp_path / "threads" / "thread-1" / "workspace"
    assert paths.uploads_dir == tmp_path / "threads" / "thread-1" / "uploads"
    assert paths.outputs_dir == tmp_path / "threads" / "thread-1" / "outputs"
    assert paths.memory_dir == tmp_path / "threads" / "thread-1" / "memory"


def test_thread_paths_ensure_creates_directories(tmp_path: Path):
    paths = ThreadPaths(thread_id="thread-1", base_dir=tmp_path).ensure()

    assert paths.workspace_dir.is_dir()
    assert paths.uploads_dir.is_dir()
    assert paths.outputs_dir.is_dir()
    assert paths.memory_dir.is_dir()


def test_thread_paths_resolve_output_and_artifact_paths(tmp_path: Path):
    paths = ThreadPaths(thread_id="thread-1", base_dir=tmp_path).ensure()

    report_path = paths.resolve_output_path("reports/final.md")
    artifact_path = paths.resolve_artifact_path("outputs/report.md")

    assert report_path == tmp_path / "threads" / "thread-1" / "outputs" / "reports" / "final.md"
    assert artifact_path == tmp_path / "threads" / "thread-1" / "outputs" / "report.md"
    assert paths.to_project_relative(artifact_path) == "threads/thread-1/outputs/report.md"


def test_store_upload_file_copies_into_thread_uploads(tmp_path: Path):
    source = tmp_path / "source.md"
    source.write_text("content", encoding="utf-8")

    uploaded_file = store_upload_file(source, thread_id="thread-1", base_dir=tmp_path / ".deerflow")

    assert uploaded_file.name == "source.md"
    assert uploaded_file.uri == "upload://source.md"
    assert uploaded_file.path == "threads/thread-1/uploads/source.md"
    assert uploaded_file.size == len("content")
    assert (tmp_path / ".deerflow" / "threads" / "thread-1" / "uploads" / "source.md").read_text(
        encoding="utf-8"
    ) == "content"


def test_store_upload_files_deduplicates_target_names(tmp_path: Path):
    first = tmp_path / "a" / "source.md"
    second = tmp_path / "b" / "source.md"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("first", encoding="utf-8")
    second.write_text("second", encoding="utf-8")

    uploaded_files = store_upload_files([first, second], thread_id="thread-1", base_dir=tmp_path / ".deerflow")

    assert [uploaded_file.uri for uploaded_file in uploaded_files] == [
        "upload://source.md",
        "upload://source-1.md",
    ]
