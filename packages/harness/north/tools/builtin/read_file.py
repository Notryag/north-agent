from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from ...resources import resolve_resource_uri
from .._runtime import resolve_runtime_path, resolve_thread_id


def resolve_readable_path(
    path: str,
    *,
    thread_id: str,
    skills_dir: Path | None,
    thread_base_dir: Path,
) -> Path:
    resolved_path = resolve_resource_uri(
        path,
        thread_id=thread_id,
        skills_dir=skills_dir,
        thread_base_dir=thread_base_dir,
    )
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")
    if not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {resolved_path}")
    return resolved_path


def read_text_file(
    path: str,
    *,
    thread_id: str,
    skills_dir: Path | None,
    thread_base_dir: Path,
) -> str:
    resolved_path = resolve_readable_path(
        path,
        thread_id=thread_id,
        skills_dir=skills_dir,
        thread_base_dir=thread_base_dir,
    )
    return resolved_path.read_text(encoding="utf-8")


@tool
def read_file(
    *,
    runtime: ToolRuntime,
    path: str,
) -> str:
    """Read a UTF-8 text file using a resource URI like skill://, upload://, workspace://, output://, or memory://."""
    try:
        skills_dir = None
        if isinstance(runtime.context, dict):
            value = runtime.context.get("skills_dir")
            if isinstance(value, (str, Path)) and value:
                skills_dir = Path(value).expanduser().resolve()

        return read_text_file(
            path,
            thread_id=resolve_thread_id(None, runtime),
            skills_dir=skills_dir,
            thread_base_dir=resolve_runtime_path("thread_base_dir", runtime),
        )
    except Exception as exc:
        return f"Read file failed: {exc}"
