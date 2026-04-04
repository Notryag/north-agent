from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage


class ToolErrorHandlingMiddleware(AgentMiddleware):
    """Return a safe fallback response when model execution fails."""

    def wrap_model_call(self, request, handler):
        try:
            return handler(request)
        except Exception as exc:
            return AIMessage(content=f"Tool or model execution failed: {exc}")
