from __future__ import annotations

from .builtin.clarification import ask_clarification
from .builtin.fetch import web_fetch
from .builtin.present_files import present_files
from .builtin.search import web_search
from .builtin.write_report import write_report


def get_builtin_tools() -> list:
    """Return the minimal built-in tool set for the lite runtime."""
    return [
        ask_clarification,
        web_search,
        web_fetch,
        write_report,
        present_files,
    ]
