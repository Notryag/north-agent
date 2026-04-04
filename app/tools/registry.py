from __future__ import annotations

from .builtin.clarification import ask_clarification
from .builtin.present_files import present_files


def get_builtin_tools() -> list:
    """Return the minimal built-in tool set for the lite runtime."""
    return [
        ask_clarification,
        present_files,
    ]
