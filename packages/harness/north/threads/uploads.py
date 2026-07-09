from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from .paths import ThreadPaths


@dataclass(frozen=True, slots=True)
class UploadedFile:
    name: str
    uri: str
    path: str
    size: int

    def as_state_record(self) -> dict:
        return {
            "name": self.name,
            "uri": self.uri,
            "path": self.path,
            "size": self.size,
        }


def _next_available_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    index = 1
    while True:
        next_candidate = directory / f"{stem}-{index}{suffix}"
        if not next_candidate.exists():
            return next_candidate
        index += 1


def store_upload_file(
    source: str | Path,
    *,
    thread_id: str,
    base_dir: Path | None = None,
) -> UploadedFile:
    source_path = Path(source).expanduser().resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"Upload file not found: {source}")
    if not source_path.is_file():
        raise ValueError(f"Upload path is not a file: {source}")

    thread_paths = ThreadPaths(thread_id=thread_id, base_dir=base_dir) if base_dir is not None else ThreadPaths(thread_id=thread_id)
    thread_paths = thread_paths.ensure()
    target_path = _next_available_path(thread_paths.uploads_dir, source_path.name)
    shutil.copy2(source_path, target_path)

    return UploadedFile(
        name=target_path.name,
        uri=f"upload://{target_path.name}",
        path=thread_paths.to_project_relative(target_path),
        size=target_path.stat().st_size,
    )


def store_upload_files(
    sources: list[str | Path] | tuple[str | Path, ...],
    *,
    thread_id: str,
    base_dir: Path | None = None,
) -> list[UploadedFile]:
    return [store_upload_file(source, thread_id=thread_id, base_dir=base_dir) for source in sources]
