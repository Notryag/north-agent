from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, HumanMessage


class ClarificationMiddleware(AgentMiddleware):
    """Ask for clarification when the latest user input is too thin to act on."""

    def wrap_model_call(self, request, handler):
        last_human = self._last_human_message(request.state.get("messages", []))
        if last_human is not None and self._needs_clarification(last_human.content):
            return AIMessage(content="Please provide a little more detail so I can respond accurately.")
        return handler(request)

    @staticmethod
    def _last_human_message(messages):
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                return msg
        return None

    @staticmethod
    def _needs_clarification(content) -> bool:
        if not isinstance(content, str):
            return False
        text = content.strip()
        if not text:
            return True
        return len(text) < 4
