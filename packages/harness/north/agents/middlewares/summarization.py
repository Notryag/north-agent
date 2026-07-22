from __future__ import annotations

import inspect
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Literal

from langchain.agents.middleware import SummarizationMiddleware
from langchain_core.messages import AnyMessage, RemoveMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES

logger = logging.getLogger(__name__)

CompactionKind = Literal["normal", "emergency"]


@dataclass(frozen=True, slots=True)
class CompactionEvent:
    summary_text: str
    summarized_messages: tuple[AnyMessage, ...]
    preserved_messages: tuple[AnyMessage, ...]
    run_id: str | None = None
    kind: CompactionKind = "normal"
    sequence: int = 1
    history_tokens: int = 0
    context_tokens: int = 0


CompactionHook = Callable[[CompactionEvent], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class _CompactionPlan:
    run_id: str
    kind: CompactionKind
    summarized: list[AnyMessage]
    preserved: list[AnyMessage]
    normal_done: bool
    emergency_count: int
    history_tokens: int
    context_tokens: int


class NorthSummarizationMiddleware(SummarizationMiddleware):
    """Run-aware history compaction with a bounded emergency path."""

    def __init__(
        self,
        model,
        *,
        normal_trigger_tokens: int = 6000,
        emergency_trigger_tokens: int = 12000,
        message_ceiling: int = 60,
        target_tokens: int = 2000,
        min_growth_tokens: int = 3000,
        max_emergency_compactions: int = 2,
        context_token_overhead: int = 0,
        compaction_hooks: list[CompactionHook] | None = None,
        **kwargs,
    ) -> None:
        values = {
            "normal_trigger_tokens": normal_trigger_tokens,
            "emergency_trigger_tokens": emergency_trigger_tokens,
            "message_ceiling": message_ceiling,
            "target_tokens": target_tokens,
            "min_growth_tokens": min_growth_tokens,
            "max_emergency_compactions": max_emergency_compactions,
        }
        for name, value in values.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than 0")
        if context_token_overhead < 0:
            raise ValueError("context_token_overhead cannot be negative")
        if emergency_trigger_tokens <= normal_trigger_tokens:
            raise ValueError(
                "emergency_trigger_tokens must be greater than normal_trigger_tokens"
            )

        super().__init__(
            model,
            trigger=None,
            keep=("tokens", target_tokens),
            **kwargs,
        )
        self.normal_trigger_tokens = normal_trigger_tokens
        self.emergency_trigger_tokens = emergency_trigger_tokens
        self.message_ceiling = message_ceiling
        self.min_growth_tokens = min_growth_tokens
        self.max_emergency_compactions = max_emergency_compactions
        self.context_token_overhead = context_token_overhead
        self.compaction_hooks = tuple(compaction_hooks or ())

    def before_model(self, state, runtime) -> dict[str, Any] | None:
        prepared, tracking_update = self._prepare(state, runtime)
        if prepared is None:
            return tracking_update
        summary = self._create_summary(prepared.summarized)
        self._run_sync_hooks(self._event(summary, prepared))
        return self._state_update(summary, prepared)

    async def abefore_model(self, state, runtime) -> dict[str, Any] | None:
        prepared, tracking_update = self._prepare(state, runtime)
        if prepared is None:
            return tracking_update
        summary = await self._acreate_summary(prepared.summarized)
        await self._run_async_hooks(self._event(summary, prepared))
        return self._state_update(summary, prepared)

    def _prepare(
        self,
        state,
        runtime,
    ) -> tuple[_CompactionPlan | None, dict[str, Any] | None]:
        messages = state["messages"]
        self._ensure_message_ids(messages)
        run_id = _runtime_run_id(runtime)
        new_run = "compaction_run_id" not in state or state.get("compaction_run_id") != run_id
        normal_done = bool(state.get("normal_compaction_done", False)) if not new_run else False
        emergency_count = int(state.get("emergency_compaction_count", 0)) if not new_run else 0
        retained_tokens = state.get("compaction_retained_tokens") if not new_run else None
        history_tokens = self.token_counter(messages)
        context_tokens = history_tokens + self.context_token_overhead

        tracking_update = None
        if new_run:
            tracking_update = {
                "compaction_run_id": run_id,
                "normal_compaction_done": False,
                "emergency_compaction_count": 0,
                "compaction_retained_tokens": None,
            }

        normal_due = new_run and (
            history_tokens >= self.normal_trigger_tokens
            or len(messages) >= self.message_ceiling
        )
        growth_since_compaction = (
            history_tokens - retained_tokens
            if isinstance(retained_tokens, int)
            else None
        )
        growth_allows_emergency = (
            growth_since_compaction is None
            or growth_since_compaction >= self.min_growth_tokens
        )
        emergency_due = (
            context_tokens >= self.emergency_trigger_tokens
            and emergency_count < self.max_emergency_compactions
            and growth_allows_emergency
        )

        if normal_due:
            kind: CompactionKind = "normal"
            normal_done = True
        elif emergency_due:
            kind = "emergency"
            emergency_count += 1
        else:
            return None, tracking_update

        cutoff = self._determine_cutoff_index(messages)
        if cutoff <= 0:
            return None, tracking_update
        summarized, preserved = self._partition_messages(messages, cutoff)
        return (
            _CompactionPlan(
                run_id=run_id,
                kind=kind,
                summarized=summarized,
                preserved=preserved,
                normal_done=normal_done,
                emergency_count=emergency_count,
                history_tokens=history_tokens,
                context_tokens=context_tokens,
            ),
            tracking_update,
        )

    def _state_update(self, summary: str, plan: _CompactionPlan) -> dict[str, Any]:
        new_messages = [*self._build_new_messages(summary), *plan.preserved]
        return {
            "messages": [
                RemoveMessage(id=REMOVE_ALL_MESSAGES),
                *new_messages,
            ],
            "summary_text": summary,
            "compaction_run_id": plan.run_id,
            "normal_compaction_done": plan.normal_done,
            "emergency_compaction_count": plan.emergency_count,
            "compaction_retained_tokens": self.token_counter(new_messages),
        }

    def _event(self, summary: str, plan: _CompactionPlan) -> CompactionEvent:
        sequence = int(plan.normal_done) + plan.emergency_count
        return CompactionEvent(
            summary_text=summary,
            summarized_messages=tuple(plan.summarized),
            preserved_messages=tuple(plan.preserved),
            run_id=plan.run_id,
            kind=plan.kind,
            sequence=sequence,
            history_tokens=plan.history_tokens,
            context_tokens=plan.context_tokens,
        )

    def _run_sync_hooks(self, event: CompactionEvent) -> None:
        for hook in self.compaction_hooks:
            try:
                result = hook(event)
                if inspect.isawaitable(result):
                    if inspect.iscoroutine(result):
                        result.close()
                    logger.warning("Async compaction hook skipped during sync invocation")
            except Exception:
                logger.exception("Compaction hook failed")

    async def _run_async_hooks(self, event: CompactionEvent) -> None:
        for hook in self.compaction_hooks:
            try:
                result = hook(event)
                if inspect.isawaitable(result):
                    await result
            except Exception:
                logger.exception("Compaction hook failed")


def _runtime_run_id(runtime) -> str:
    context = getattr(runtime, "context", None)
    if isinstance(context, dict):
        run_id = context.get("run_id")
        if run_id is not None:
            return str(run_id)
    return "__unscoped__"
