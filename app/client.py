from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .agent import build_agent
from .config import AppConfig


@dataclass(slots=True)
class StreamEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


class ChatResponse(str):
    thread_id: str | None
    artifacts: tuple[str, ...]

    def __new__(
        cls,
        content: str,
        *,
        thread_id: str | None,
        artifacts: tuple[str, ...] = (),
    ) -> "ChatResponse":
        response = super().__new__(cls, content)
        response.thread_id = thread_id
        response.artifacts = artifacts
        return response


class AppClient:
    def __init__(self, config: AppConfig, *, checkpointer=None):
        self.config = config
        self.checkpointer = checkpointer
        self._agent = None

    def _get_agent(self):
        if self._agent is None:
            self._agent = build_agent(self.config, checkpointer=self.checkpointer)
        return self._agent

    def _get_runnable_config(self, thread_id: str) -> RunnableConfig:
        return RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=self.config.recursion_limit,
        )

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, str):
                    parts.append(block)
                    continue
                if isinstance(block, dict):
                    text = block.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "\n".join(part for part in parts if part)
        return str(content)

    @staticmethod
    def _extract_artifacts(chunk: dict[str, Any]) -> tuple[str, ...]:
        value = chunk.get("artifacts", [])
        if not isinstance(value, list):
            return ()
        return tuple(item for item in value if isinstance(item, str))

    def stream(self, message: str, *, thread_id: str | None = None) -> Generator[StreamEvent, None, None]:
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        agent = self._get_agent()
        config = self._get_runnable_config(thread_id)
        state = {"messages": [HumanMessage(content=message)]}
        seen_ai_ids: set[str] = set()
        seen_tool_ids: set[tuple[str | None, str | None, str]] = set()
        latest_artifacts: tuple[str, ...] = ()
        context = {"thread_id": thread_id}

        try:
            for chunk in agent.stream(state, config=config, context=context, stream_mode="values"):
                messages = chunk.get("messages", [])
                artifacts = self._extract_artifacts(chunk)
                if artifacts:
                    latest_artifacts = artifacts

                for msg in messages:
                    if isinstance(msg, AIMessage):
                        msg_id = getattr(msg, "id", None)
                        if msg_id and msg_id in seen_ai_ids:
                            continue
                        if msg_id:
                            seen_ai_ids.add(msg_id)

                        text = self._extract_text(msg.content)
                        if not text:
                            continue
                        yield StreamEvent(
                            type="ai",
                            data={
                                "role": "ai",
                                "content": text,
                                "thread_id": thread_id,
                                "artifacts": latest_artifacts,
                            },
                        )
                        continue

                    if not isinstance(msg, ToolMessage):
                        continue

                    text = self._extract_text(msg.content)
                    tool_key = (msg.tool_call_id, getattr(msg, "name", None), text)
                    if tool_key in seen_tool_ids:
                        continue
                    seen_tool_ids.add(tool_key)

                    yield StreamEvent(
                        type="tool",
                        data={
                            "name": getattr(msg, "name", None),
                            "content": text,
                            "tool_call_id": msg.tool_call_id,
                            "status": getattr(msg, "status", "success"),
                            "thread_id": thread_id,
                            "artifacts": latest_artifacts,
                        },
                    )

                yield StreamEvent(
                    type="values",
                    data={"thread_id": thread_id, "chunk": chunk, "artifacts": latest_artifacts},
                )
        except Exception as exc:
            yield StreamEvent(
                type="error",
                data={"thread_id": thread_id, "message": str(exc), "error_type": type(exc).__name__},
            )
            raise

        yield StreamEvent(type="end", data={"thread_id": thread_id, "artifacts": latest_artifacts})

    def chat(self, message: str, *, thread_id: str | None = None) -> ChatResponse:
        last_text = ""
        final_thread_id = thread_id
        artifacts: tuple[str, ...] = ()
        for event in self.stream(message, thread_id=thread_id):
            event_thread_id = event.data.get("thread_id")
            if isinstance(event_thread_id, str):
                final_thread_id = event_thread_id
            if event.type == "ai":
                last_text = event.data["content"]
            event_artifacts = event.data.get("artifacts")
            if isinstance(event_artifacts, tuple):
                artifacts = event_artifacts
        return ChatResponse(last_text, thread_id=final_thread_id, artifacts=artifacts)
