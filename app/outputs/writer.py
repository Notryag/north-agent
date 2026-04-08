from __future__ import annotations

from pathlib import Path

from ..threads import ThreadPaths


def _resolve_output_path(thread_id: str, filename: str, *, base_dir: Path | None = None) -> Path:
    relative_path = Path(filename)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Invalid output filename: {filename}")

    paths = ThreadPaths(thread_id=thread_id, base_dir=base_dir) if base_dir is not None else ThreadPaths(thread_id=thread_id)
    paths = paths.ensure()
    output_path = paths.outputs_dir / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


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
