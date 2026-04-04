from langchain_core.tools import tool


@tool
def ask_clarification(question: str) -> str:
    """Ask the user for the missing detail needed to continue."""
    return f"Clarification needed: {question}"
