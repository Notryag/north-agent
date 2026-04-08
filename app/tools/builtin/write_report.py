from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from ...outputs.writer import write_output_file
from ...threads import ThreadPaths
from .._runtime import resolve_thread_id


def write_report_file(
    content: str,
    *,
    filename: str = "report.md",
    thread_id: str = "default",
    base_dir: Path | None = None,
) -> Path:
    """Write a report file into the thread outputs directory."""
    return write_output_file(
        thread_id=thread_id,
        filename=filename,
        content=content,
        base_dir=base_dir,
    )


@tool
def write_report(
    *,
    content: str,
    filename: str = "report.md",
    runtime: ToolRuntime | None = None,
) -> str:
    """Write a Markdown report into the current thread outputs directory."""
    resolved_thread_id = resolve_thread_id(None, runtime)
    try:
        output_path = write_report_file(
            content=content,
            filename=filename,
            thread_id=resolved_thread_id,
        )
    except Exception as exc:
        return f"Report write failed: {exc}"
    relative_output_path = ThreadPaths(thread_id=resolved_thread_id).to_project_relative(output_path)
    return f"Report written to {relative_output_path}"
