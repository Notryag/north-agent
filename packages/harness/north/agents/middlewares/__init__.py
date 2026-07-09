from .clarification import ClarificationMiddleware
from .loop_detection import LoopDetectionMiddleware
from .tool_error import ToolErrorHandlingMiddleware


def get_default_middlewares():
    return [
        ToolErrorHandlingMiddleware(),
        LoopDetectionMiddleware(),
        ClarificationMiddleware(),
    ]


__all__ = [
    "ClarificationMiddleware",
    "LoopDetectionMiddleware",
    "ToolErrorHandlingMiddleware",
    "get_default_middlewares",
]
