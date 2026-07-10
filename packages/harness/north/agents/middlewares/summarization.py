from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AnyMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class CompactionEvent:
    summary_text: str
    summarized_messages: tuple[AnyMessage, ...]
    preserved_messages: tuple[AnyMessage, ...]


CompactionHook = Callable[[CompactionEvent], Awaitable[None] | None]


class NorthSummarizationMiddleware(SummarizationMiddleware):
    """LangChain summarization with durable summary state and host hooks."""

    def __init__(self, *args, compaction_hooks: list[CompactionHook] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.compaction_hooks = tuple(compaction_hooks or ())

    def before_model(self, state, runtime) -> dict[str, Any] | None:
        prepared = self._prepare(state)
        if prepared is None:
            return None
        summarized, preserved = prepared
        summary = self._create_summary(summarized)
        event = CompactionEvent(summary, tuple(summarized), tuple(preserved))
        for hook in self.compaction_hooks:
            try:
                result = hook(event)
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    logger.warning("Async compaction hook skipped during sync invocation")
            except Exception:
                logger.exception("Compaction hook failed")
        return self._state_update(summary, preserved)

    async def abefore_model(self, state, runtime) -> dict[str, Any] | None:
        prepared = self._prepare(state)
        if prepared is None:
            return None
        summarized, preserved = prepared
        summary = await self._acreate_summary(summarized)
        event = CompactionEvent(summary, tuple(summarized), tuple(preserved))
        for hook in self.compaction_hooks:
            try:
                result = hook(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Compaction hook failed")
        return self._state_update(summary, preserved)

    def _prepare(self, state) -> tuple[list[AnyMessage], list[AnyMessage]] | None:
        messages = state["messages"]
        self._ensure_message_ids(messages)
        if not self._should_summarize(messages, self.token_counter(messages)):
            return None
        cutoff = self._determine_cutoff_index(messages)
        if cutoff <= 0:
            return None
        return self._partition_messages(messages, cutoff)

    def _state_update(self, summary: str, preserved: list[AnyMessage]) -> dict[str, Any]:
        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *self._build_new_messages(summary),
                *preserved,
            ],
            "summary_text": summary,
        }
