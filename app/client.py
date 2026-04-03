from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import RunnableConfig

from .agent import build_agent
from .config import AppConfig


@dataclass(slots=True)
class StreamEvent:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


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

    def stream(self, message: str, *, thread_id: str | None = None) -> Generator[StreamEvent, None, None]:
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        agent = self._get_agent()
        config = self._get_runnable_config(thread_id)
        state = {"messages": [HumanMessage(content=message)]}
        seen_ids: set[str] = set()
        context = {"thread_id": thread_id}

        try:
            for chunk in agent.stream(state, config=config, context=context, stream_mode="values"):
                messages = chunk.get("messages", [])
                for msg in messages:
                    if not isinstance(msg, AIMessage):
                        continue

                    msg_id = getattr(msg, "id", None)
                    if msg_id and msg_id in seen_ids:
                        continue
                    if msg_id:
                        seen_ids.add(msg_id)

                    text = self._extract_text(msg.content)
                    if text:
                        yield StreamEvent(
                            type="ai",
                            data={"role": "ai", "content": text, "thread_id": thread_id},
                        )

                yield StreamEvent(type="values", data={"thread_id": thread_id, "chunk": chunk})
        except Exception as exc:
            yield StreamEvent(
                type="error",
                data={"thread_id": thread_id, "message": str(exc), "error_type": type(exc).__name__},
            )
            raise

        yield StreamEvent(type="end", data={"thread_id": thread_id})

    def chat(self, message: str, *, thread_id: str | None = None) -> str:
        last_text = ""
        for event in self.stream(message, thread_id=thread_id):
            if event.type == "ai":
                last_text = event.data["content"]
        return last_text
