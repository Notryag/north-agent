from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage


class LoopDetectionMiddleware(AgentMiddleware):
    """Detect repeated responses and replace them with a loop warning."""

    def wrap_model_call(self, request, handler):
        response = handler(request)
        if not response.result:
            return response

        latest = response.result[0]
        if not isinstance(latest, AIMessage):
            return response

        previous_text = self._last_ai_text(request.state.get("messages", []))
        current_text = self._extract_text(latest.content)
        if previous_text and previous_text == current_text:
            return AIMessage(content="Loop detected. Please provide a different response or more context.")
        return response

    @staticmethod
    def _last_ai_text(messages) -> str:
        for msg in reversed(messages):
            if isinstance(msg, AIMessage):
                return LoopDetectionMiddleware._extract_text(msg.content)
        return ""

    @staticmethod
    def _extract_text(content) -> str:
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                elif isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(part for part in parts if part).strip()
        return str(content).strip()
