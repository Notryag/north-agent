from typing import NotRequired

from langchain.agents import AgentState


class ThreadState(AgentState):
    """Compact shared state for the lite runtime."""

    title: NotRequired[str | None]
    artifacts: NotRequired[list[str]]
    thread_data: NotRequired[dict | None]
    uploaded_files: NotRequired[list[dict] | None]
