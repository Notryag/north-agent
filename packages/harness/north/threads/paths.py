from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _normalize_relative_path(path: str | Path) -> Path:
    candidate = Path(path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"Invalid thread-relative path: {path}")
    return candidate


@dataclass(frozen=True, slots=True)
class ThreadPaths:
    thread_id: str
    base_dir: Path

    @property
    def threads_dir(self) -> Path:
        return self.base_dir / "threads"

    @property
    def thread_dir(self) -> Path:
        return self.threads_dir / self.thread_id

    @property
    def workspace_dir(self) -> Path:
        return self.thread_dir / "workspace"

    @property
    def uploads_dir(self) -> Path:
        return self.thread_dir / "uploads"

    @property
    def outputs_dir(self) -> Path:
        return self.thread_dir / "outputs"

    @property
    def memory_dir(self) -> Path:
        return self.thread_dir / "memory"

    def resolve_output_path(self, filename: str | Path) -> Path:
        relative_path = _normalize_relative_path(filename)
        output_path = self.outputs_dir / relative_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path

    def resolve_artifact_path(self, path: str | Path) -> Path:
        relative_path = _normalize_relative_path(path)
        if relative_path.parts[:1] == ("outputs",):
            artifact_path = self.thread_dir / relative_path
        else:
            artifact_path = self.outputs_dir / relative_path
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        return artifact_path

    def to_project_relative(self, path: Path) -> str:
        resolved_path = path.resolve()
        try:
            return resolved_path.relative_to(self.base_dir.resolve()).as_posix()
        except ValueError:
            pass
        return resolved_path.as_posix()

    def ensure(self) -> "ThreadPaths":
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        return self
