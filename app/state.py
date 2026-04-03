from langchain.agents import AgentState


class ThreadState(AgentState):
    """Minimal thread state that relies on AgentState.messages."""

    pass
