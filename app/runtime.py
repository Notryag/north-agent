from __future__ import annotations

from collections.abc import Sequence

from langchain.agents.middleware import AgentMiddleware

from .agents.middlewares import get_default_middlewares
from .checkpointer import get_default_checkpointer
from .config import AppConfig
from .state import ThreadState
from .tools import get_builtin_tools


def get_tools(config: AppConfig) -> list:
    """Resolve runtime tools for the given config."""
    _ = config
    return get_builtin_tools()


def get_middlewares(config: AppConfig) -> Sequence[AgentMiddleware]:
    """Resolve runtime middlewares for the given config."""
    _ = config
    return get_default_middlewares()


def get_checkpointer(config: AppConfig):
    """Resolve the default checkpointer for the given config."""
    _ = config
    return get_default_checkpointer()


def get_state_schema():
    """Resolve the shared state schema for the lite runtime.

    ``ThreadState`` intentionally stays narrow in this phase so tools only need
    one stable write surface: ``artifacts``.
    """
    return ThreadState
