from pathlib import Path

from app.threads.paths import ThreadPaths


def test_thread_paths_resolve_expected_directories(tmp_path: Path):
    paths = ThreadPaths(thread_id="thread-1", base_dir=tmp_path)

    assert paths.thread_dir == tmp_path / "threads" / "thread-1"
    assert paths.workspace_dir == tmp_path / "threads" / "thread-1" / "workspace"
    assert paths.uploads_dir == tmp_path / "threads" / "thread-1" / "uploads"
    assert paths.outputs_dir == tmp_path / "threads" / "thread-1" / "outputs"


def test_thread_paths_ensure_creates_directories(tmp_path: Path):
    paths = ThreadPaths(thread_id="thread-1", base_dir=tmp_path).ensure()

    assert paths.workspace_dir.is_dir()
    assert paths.uploads_dir.is_dir()
    assert paths.outputs_dir.is_dir()
