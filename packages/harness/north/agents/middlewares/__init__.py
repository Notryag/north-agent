from .clarification import ClarificationMiddleware
from .loop_detection import LoopDetectionMiddleware
from .tool_error import ToolErrorHandlingMiddleware
from .summarization import CompactionEvent, CompactionHook, NorthSummarizationMiddleware


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
    "CompactionEvent",
    "CompactionHook",
    "NorthSummarizationMiddleware",
    "get_default_middlewares",
]
