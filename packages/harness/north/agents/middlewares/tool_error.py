from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage


class ToolErrorHandlingMiddleware(AgentMiddleware):
    """Convert tool exceptions into error ToolMessages."""

    def wrap_tool_call(self, request, handler):
        try:
            return handler(request)
        except Exception as exc:
            tool_name = request.tool_call.get("name", "unknown_tool")
            return ToolMessage(
                content=f"Tool '{tool_name}' failed: {exc}",
                tool_call_id=request.tool_call["id"],
                name=tool_name,
                status="error",
            )

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as exc:
            tool_name = request.tool_call.get("name", "unknown_tool")
            return ToolMessage(
                content=f"Tool '{tool_name}' failed: {exc}",
                tool_call_id=request.tool_call["id"],
                name=tool_name,
                status="error",
            )
