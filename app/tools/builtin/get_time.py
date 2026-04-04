from __future__ import annotations

from datetime import UTC, datetime

from langchain_core.tools import tool


@tool
def get_time() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(UTC).isoformat()
