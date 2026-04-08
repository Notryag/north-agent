from __future__ import annotations

import json

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import AIMessage, ToolMessage


def _tool_signature(tool_call: dict) -> tuple[str, str]:
    return (
        tool_call.get("name", ""),
        json.dumps(tool_call.get("args", {}), sort_keys=True, ensure_ascii=True, default=str),
    )


class LoopDetectionMiddleware(AgentMiddleware):
    """Block repeated identical tool calls before the loop grows."""

    def __init__(self, *, max_same_call_count: int = 2) -> None:
        self.max_same_call_count = max_same_call_count

    def _seen_call_count(self, state, tool_call: dict) -> int:
        if not isinstance(state, dict):
            return 0

        messages = state.get("messages", [])
        if not isinstance(messages, list):
            return 0

        signature = _tool_signature(tool_call)
        count = 0

        for message in messages:
            if not isinstance(message, AIMessage):
                continue
            tool_calls = getattr(message, "tool_calls", [])
            if not isinstance(tool_calls, list):
                continue
            count += sum(1 for item in tool_calls if _tool_signature(item) == signature)

        return count

    def wrap_tool_call(self, request, handler):
        count = self._seen_call_count(request.state, request.tool_call)
        if count > self.max_same_call_count:
            tool_name = request.tool_call.get("name", "unknown_tool")
            return ToolMessage(
                content=f"Stopped repeated tool loop for '{tool_name}' after {count} identical calls.",
                tool_call_id=request.tool_call["id"],
                name=tool_name,
                status="error",
            )
        return handler(request)
