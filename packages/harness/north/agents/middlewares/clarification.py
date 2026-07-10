from __future__ import annotations

from copy import deepcopy

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command


def _merge_thread_data(existing, updates: dict) -> dict:
    merged = dict(existing) if isinstance(existing, dict) else {}
    merged.update(updates)
    return merged


def _clear_clarification(existing) -> dict | None:
    if not isinstance(existing, dict):
        return None

    updated = deepcopy(existing)
    updated.pop("clarification", None)
    return updated or None


class ClarificationMiddleware(AgentMiddleware):
    """Track clarification requests in thread_data and clear them on user reply."""

    def before_model(self, state, runtime):
        if not isinstance(state, dict):
            return None

        thread_data = state.get("thread_data")
        if not isinstance(thread_data, dict) or "clarification" not in thread_data:
            return None

        messages = state.get("messages", [])
        if not isinstance(messages, list) or not messages:
            return None

        if isinstance(messages[-1], HumanMessage):
            return {"thread_data": _clear_clarification(thread_data)}

        return None

    def wrap_tool_call(self, request, handler):
        result = handler(request)
        return self._track_clarification(request, result)

    async def awrap_tool_call(self, request, handler):
        result = await handler(request)
        return self._track_clarification(request, result)

    def _track_clarification(self, request, result):
        if request.tool_call.get("name") != "ask_clarification":
            return result

        question = request.tool_call.get("args", {}).get("question")
        if not isinstance(question, str) or not question:
            question = "More information is required to continue."

        if isinstance(result, ToolMessage):
            return Command(
                update={
                    "thread_data": _merge_thread_data(
                        request.state.get("thread_data") if isinstance(request.state, dict) else None,
                        {"clarification": {"status": "pending", "question": question}},
                    ),
                    "messages": [result],
                }
            )

        if isinstance(result, Command) and isinstance(result.update, dict):
            update = deepcopy(result.update)
            update["thread_data"] = _merge_thread_data(
                request.state.get("thread_data") if isinstance(request.state, dict) else None,
                {"clarification": {"status": "pending", "question": question}},
            )
            return Command(graph=result.graph, update=update, resume=result.resume, goto=result.goto)

        return result
