from typing import Literal

from langchain_core.tools import tool


@tool
def ask_clarification(
    question: str,
    response_kind: Literal["free_text", "single_choice"] = "free_text",
    options: list[str] | None = None,
) -> str:
    """Ask for a missing detail, optionally with concise choices.

    Args:
        question: The specific question the user needs to answer.
        response_kind: Use single_choice only when a short set of useful choices exists.
        options: Choice labels for single_choice; omit for free_text.
    """
    return f"Clarification needed: {question}"
