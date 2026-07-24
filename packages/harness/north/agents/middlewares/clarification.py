from __future__ import annotations

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import HumanMessage, ToolMessage
from langgraph.types import Command


class ClarificationMiddleware(AgentMiddleware):
    """Expose a typed clarification request and clear it on user reply."""

    def before_model(self, state, runtime):
        if not isinstance(state, dict):
            return None

        if not isinstance(state.get("clarification_request"), dict):
            return None

        messages = state.get("messages", [])
        if not isinstance(messages, list) or not messages:
            return None

        if isinstance(messages[-1], HumanMessage):
            return {"clarification_request": None}

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

        args = request.tool_call.get("args", {})
        question = args.get("question")
        if not isinstance(question, str) or not question.strip():
            question = "More information is required to continue."
        else:
            question = question.strip()

        response_kind = args.get("response_kind", "free_text")
        if response_kind not in {"free_text", "single_choice"}:
            response_kind = "free_text"
        options = args.get("options")
        if not isinstance(options, list):
            options = []
        options = [
            option.strip() for option in options if isinstance(option, str) and option.strip()
        ][:10]
        if response_kind == "single_choice" and not options:
            response_kind = "free_text"
        clarification_request = {
            "question": question,
            "response_kind": response_kind,
            "options": options if response_kind == "single_choice" else [],
        }

        if isinstance(result, ToolMessage):
            return Command(
                update={
                    "clarification_request": clarification_request,
                    "messages": [result],
                }
            )

        if isinstance(result, Command) and isinstance(result.update, dict):
            update = dict(result.update)
            update["clarification_request"] = clarification_request
            return Command(graph=result.graph, update=update, resume=result.resume, goto=result.goto)

        return result
