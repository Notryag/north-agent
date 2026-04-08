from typing import Any, Final, NotRequired

from langchain.agents import AgentState

THREAD_STATE_UPDATE_GUIDE: Final[dict[str, str]] = {
    "title": "Reserved for runtime-level metadata. Tools should not write this field in the current stage.",
    "artifacts": "Thread-scoped artifact paths. Tools may append generated files; runtime reads and exposes them through chat/stream.",
    "thread_data": "Runtime-owned scratch metadata for future workspace/file flows. General tools should treat it as read-only unless a dedicated contract is introduced.",
    "uploaded_files": "Runtime-owned records for user-provided files. Tools may consume these records but should not mutate them directly.",
}


class ThreadState(AgentState):
    """Compact shared state for the lite runtime.

    The current stage keeps this schema intentionally small:

    - ``artifacts`` is the only field that regular tools are expected to update.
    - ``thread_data`` and ``uploaded_files`` stay runtime-owned until a stronger
      file/workspace contract exists.
    - ``thread_id`` is not stored here; it remains runnable context used to
      scope checkpoints and artifact paths.
    """

    title: NotRequired[str | None]
    artifacts: NotRequired[list[str]]
    thread_data: NotRequired[dict[str, Any] | None]
    uploaded_files: NotRequired[list[dict] | None]
