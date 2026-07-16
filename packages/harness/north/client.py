from __future__ import annotations

import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .agent import build_agent
from .config import AppConfig
from .runtime import RuntimeService
from .threads import store_upload_files


@dataclass(slots=True)
class StreamEvent:
    """Normalized client event.

    Event types used by the current runtime:
    - ``ai``: assistant text output
    - ``tool``: tool message emitted into the graph state
    - ``values``: raw streamed state chunk
    - ``end``: terminal success marker
    - ``error``: terminal failure marker emitted before re-raising
    """

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
        self._agents: dict[tuple[str, ...], Any] = {}
        self.runtime = RuntimeService()

    def _normalize_skills(self, skills: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
        raw_items = self.config.enabled_skills if skills is None else tuple(skills)
        normalized: list[str] = []
        for raw_item in raw_items:
            item = raw_item.strip()
            if item and item not in normalized:
                normalized.append(item)
        return tuple(normalized)

    def _get_agent(self, *, skills: list[str] | tuple[str, ...] | None = None):
        skill_key = self._normalize_skills(skills)
        if not skill_key and self._agent is not None:
            return self._agent
        if skill_key not in self._agents:
            agent = build_agent(self.config, checkpointer=self.checkpointer, skills=skill_key)
            self._agents[skill_key] = agent
            if not skill_key:
                self._agent = agent
        return self._agents[skill_key]

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

    @staticmethod
    def _format_upload_notice(uploaded_files: list[dict]) -> str:
        if not uploaded_files:
            return ""
        lines = ["Available uploaded files:"]
        for uploaded_file in uploaded_files:
            uri = uploaded_file.get("uri")
            name = uploaded_file.get("name")
            if isinstance(uri, str) and isinstance(name, str):
                lines.append(f"- {uri} ({name})")
        return "\n".join(lines)

    def stream(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        skills: list[str] | tuple[str, ...] | None = None,
        files: list[str | Path] | tuple[str | Path, ...] | None = None,
    ) -> Generator[StreamEvent, None, None]:
        if thread_id is None:
            thread_id = str(uuid.uuid4())

        uploaded_files: list[dict] = []
        if files:
            if self.config.thread_base_dir is None:
                raise RuntimeError("File uploads require an explicit thread_base_dir")
            uploaded_files = [
                uploaded_file.as_state_record()
                for uploaded_file in store_upload_files(
                    files,
                    thread_id=thread_id,
                    base_dir=self.config.thread_base_dir,
                )
            ]
        upload_notice = self._format_upload_notice(uploaded_files)
        message_content = f"{message}\n\n{upload_notice}" if upload_notice else message

        config = self._get_runnable_config(thread_id)
        state: dict[str, Any] = {"messages": [HumanMessage(content=message_content)]}
        if uploaded_files:
            state["uploaded_files"] = uploaded_files
        seen_ai_ids: set[str] = set()
        seen_tool_ids: set[tuple[str | None, str | None, str]] = set()
        latest_artifacts: tuple[str, ...] = ()
        context = {"thread_id": thread_id}
        if self.config.skills_dir is not None:
            context["skills_dir"] = str(self.config.skills_dir.resolve())
        if self.config.thread_base_dir is not None:
            context["thread_base_dir"] = str(self.config.thread_base_dir.resolve())

        def agent_factory():
            return self._get_agent(skills=skills)

        record = self.runtime.start_run(
            thread_id=thread_id,
            agent_factory=agent_factory,
            graph_input=state,
            config=config,
            context=context,
            stream_mode="values",
        )

        try:
            for runtime_event in self.runtime.stream_run(record.run_id):
                if runtime_event.event == "metadata":
                    continue

                if runtime_event.event == "error":
                    error_data = runtime_event.data if isinstance(runtime_event.data, dict) else {}
                    yield StreamEvent(
                        type="error",
                        data={
                            "thread_id": thread_id,
                            "message": str(error_data.get("message") or ""),
                            "error_type": str(error_data.get("error_type") or "Error"),
                        },
                    )
                    raise RuntimeError(error_data.get("message") or "")

                if runtime_event.event == "end":
                    break

                if runtime_event.event != "values":
                    yield StreamEvent(
                        type=runtime_event.event,
                        data={"thread_id": thread_id, "data": runtime_event.data, "artifacts": latest_artifacts},
                    )
                    continue

                chunk = runtime_event.data
                if not isinstance(chunk, dict):
                    continue
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
        except RuntimeError:
            raise
        except Exception as exc:
            yield StreamEvent(
                type="error",
                data={"thread_id": thread_id, "message": str(exc), "error_type": type(exc).__name__},
            )
            raise

        yield StreamEvent(type="end", data={"thread_id": thread_id, "artifacts": latest_artifacts})

    def chat(
        self,
        message: str,
        *,
        thread_id: str | None = None,
        skills: list[str] | tuple[str, ...] | None = None,
        files: list[str | Path] | tuple[str | Path, ...] | None = None,
    ) -> ChatResponse:
        last_text = ""
        final_thread_id = thread_id
        artifacts: tuple[str, ...] = ()
        for event in self.stream(message, thread_id=thread_id, skills=skills, files=files):
            event_thread_id = event.data.get("thread_id")
            if isinstance(event_thread_id, str):
                final_thread_id = event_thread_id
            if event.type == "ai":
                last_text = event.data["content"]
            event_artifacts = event.data.get("artifacts")
            if isinstance(event_artifacts, tuple):
                artifacts = event_artifacts
        return ChatResponse(last_text, thread_id=final_thread_id, artifacts=artifacts)
