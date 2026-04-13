from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from ...config import PROJECT_ROOT
from ...threads import ThreadPaths
from .._runtime import resolve_thread_id


def _resolve_allowed_roots(runtime: ToolRuntime | None) -> tuple[Path, ...]:
    roots: list[Path] = []

    if runtime is not None and isinstance(runtime.context, dict):
        skills_dir = runtime.context.get("skills_dir")
        if isinstance(skills_dir, str) and skills_dir:
            roots.append(Path(skills_dir))

    thread_id = resolve_thread_id(None, runtime)
    roots.append(ThreadPaths(thread_id=thread_id).thread_dir)

    unique_roots: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        resolved_root = root.resolve()
        if resolved_root in seen:
            continue
        seen.add(resolved_root)
        unique_roots.append(resolved_root)
    return tuple(unique_roots)


def resolve_readable_path(path: str, *, allowed_roots: tuple[Path, ...], project_root: Path = PROJECT_ROOT) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    for root in allowed_roots:
        try:
            candidate.relative_to(root)
            return candidate
        except ValueError:
            continue
    raise ValueError(f"Path is outside allowed read roots: {path}")


def read_text_file(path: str, *, allowed_roots: tuple[Path, ...], project_root: Path = PROJECT_ROOT) -> str:
    resolved_path = resolve_readable_path(path, allowed_roots=allowed_roots, project_root=project_root)
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {resolved_path}")
    if not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {resolved_path}")
    return resolved_path.read_text(encoding="utf-8")


@tool
def read_file(
    *,
    runtime: ToolRuntime,
    path: str,
) -> str:
    """Read a UTF-8 text file from the configured skills directory or current thread directory."""
    try:
        return read_text_file(path, allowed_roots=_resolve_allowed_roots(runtime))
    except Exception as exc:
        return f"Read file failed: {exc}"
