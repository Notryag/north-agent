from __future__ import annotations

from langchain_core.tools import tool


@tool
def present_files(paths: list[str], summary: str | None = None) -> str:
    """Present output files in a compact human-readable format."""
    if not paths:
        return "No files to present."

    lines = ["Files:"]
    lines.extend(f"- {path}" for path in paths)
    if summary:
        lines.append(f"Summary: {summary}")
    return "\n".join(lines)
