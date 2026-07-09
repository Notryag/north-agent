from __future__ import annotations

from pathlib import Path

from ..threads import ThreadPaths


def _resolve_output_path(thread_id: str, filename: str, *, base_dir: Path | None = None) -> Path:
    paths = ThreadPaths(thread_id=thread_id, base_dir=base_dir) if base_dir is not None else ThreadPaths(thread_id=thread_id)
    return paths.ensure().resolve_output_path(filename)


def write_output_file(
    *,
    thread_id: str,
    filename: str,
    content: str,
    base_dir: Path | None = None,
) -> Path:
    """Write a text output file into the thread outputs directory."""
    output_path = _resolve_output_path(thread_id, filename, base_dir=base_dir)
    output_path.write_text(content, encoding="utf-8")
    return output_path
