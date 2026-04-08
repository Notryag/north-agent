from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.messages import ToolMessage
from langchain_core.tools import tool
from langgraph.types import Command

from ...threads import ThreadPaths
from .._runtime import resolve_thread_id


def _merge_artifacts(existing: list[str], new: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for artifact in [*existing, *new]:
        if artifact in seen:
            continue
        seen.add(artifact)
        merged.append(artifact)

    return merged


def _format_presented_files(paths: list[str], summary: str | None = None) -> str:
    lines = ["Files:"]
    lines.extend(f"- {path}" for path in paths)
    if summary:
        lines.append(f"Summary: {summary}")
    return "\n".join(lines)


def resolve_artifact_paths(
    paths: list[str],
    *,
    thread_id: str,
    base_dir: Path | None = None,
) -> list[str]:
    thread_paths = ThreadPaths(thread_id=thread_id, base_dir=base_dir) if base_dir is not None else ThreadPaths(thread_id=thread_id)
    thread_paths = thread_paths.ensure()

    artifacts: list[str] = []
    for path in paths:
        resolved_path = thread_paths.resolve_artifact_path(path)
        artifacts.append(thread_paths.to_project_relative(resolved_path))

    return _merge_artifacts([], artifacts)


def present_file_listing(
    paths: list[str],
    *,
    summary: str | None = None,
    thread_id: str = "default",
    base_dir: Path | None = None,
) -> str:
    artifacts = resolve_artifact_paths(paths, thread_id=thread_id, base_dir=base_dir)
    return _format_presented_files(artifacts, summary)


@tool
def present_files(
    *,
    runtime: ToolRuntime,
    paths: list[str],
    summary: str | None = None,
) -> str | Command:
    """Present output files and persist them into thread artifacts."""
    if not paths:
        return "No files to present."

    try:
        resolved_thread_id = resolve_thread_id(None, runtime)
        artifacts = resolve_artifact_paths(paths, thread_id=resolved_thread_id)
    except Exception as exc:
        return f"Present files failed: {exc}"

    message = _format_presented_files(artifacts, summary)
    if runtime.tool_call_id is None:
        return message

    existing_artifacts: list[str] = []
    if isinstance(runtime.state, dict):
        state_artifacts = runtime.state.get("artifacts", [])
        if isinstance(state_artifacts, list):
            existing_artifacts = [item for item in state_artifacts if isinstance(item, str)]

    return Command(
        update={
            "artifacts": _merge_artifacts(existing_artifacts, artifacts),
            "messages": [
                ToolMessage(
                    content=message,
                    tool_call_id=runtime.tool_call_id,
                )
            ],
        }
    )
