"""Typed product-neutral results emitted by the North runtime."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping


ClarificationResponseKind = Literal["free_text", "single_choice"]


@dataclass(frozen=True, slots=True)
class ClarificationRequest:
    question: str
    response_kind: ClarificationResponseKind = "free_text"
    options: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("Clarification question cannot be empty")
        if self.response_kind == "free_text" and self.options:
            raise ValueError("Free-text clarification cannot contain options")
        if self.response_kind == "single_choice" and not self.options:
            raise ValueError("Single-choice clarification requires options")


@dataclass(frozen=True, slots=True)
class RuntimeExecutionResult:
    values: Any
    clarification: ClarificationRequest | None = None


def clarification_from_values(values: Any) -> ClarificationRequest | None:
    if not isinstance(values, Mapping):
        return None
    raw = values.get("clarification_request")
    if not isinstance(raw, Mapping):
        return None

    question = raw.get("question")
    response_kind = raw.get("response_kind", "free_text")
    raw_options = raw.get("options", [])
    if not isinstance(question, str) or not question.strip():
        return None
    if response_kind not in {"free_text", "single_choice"}:
        return None
    if not isinstance(raw_options, list):
        return None
    options = tuple(
        option.strip()
        for option in raw_options
        if isinstance(option, str) and option.strip()
    )
    if response_kind == "single_choice" and not options:
        return None
    return ClarificationRequest(
        question=question,
        response_kind=response_kind,
        options=options if response_kind == "single_choice" else (),
    )
