from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from ...outputs.writer import write_output_file


def _resolve_thread_id(thread_id: str | None, runtime: ToolRuntime | None) -> str:
    if thread_id:
        return thread_id
    if runtime is not None and isinstance(runtime.context, dict):
        value = runtime.context.get("thread_id")
        if isinstance(value, str) and value:
            return value
    if runtime is not None:
        configurable = runtime.config.get("configurable", {})
        if isinstance(configurable, dict):
            value = configurable.get("thread_id")
            if isinstance(value, str) and value:
                return value
    return "default"


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
    runtime: ToolRuntime,
) -> str:
    """Write a Markdown report into the current thread outputs directory."""
    resolved_thread_id = _resolve_thread_id(None, runtime)
    try:
        output_path = write_report_file(
            content=content,
            filename=filename,
            thread_id=resolved_thread_id,
        )
    except Exception as exc:
        return f"Report write failed: {exc}"
    return f"Report written to {output_path.as_posix()}"
