from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .threads import ThreadPaths

RESOURCE_SCHEMES = {"skill", "upload", "workspace", "output", "memory"}


@dataclass(frozen=True, slots=True)
class ResourceUri:
    scheme: str
    value: str


def _normalize_resource_parts(uri: str) -> tuple[str, list[str]]:
    parsed = urlparse(uri)
    if parsed.scheme not in RESOURCE_SCHEMES:
        raise ValueError(f"Unsupported resource URI scheme: {parsed.scheme or '<missing>'}")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError(f"Resource URI must not include params, query, or fragment: {uri}")

    parts = [part for part in [parsed.netloc, *parsed.path.split("/")] if part]
    if not parts and parsed.scheme != "skill":
        raise ValueError(f"Resource URI is missing a path: {uri}")
    if any(part in {".", ".."} for part in parts):
        raise ValueError(f"Resource URI must not escape its domain root: {uri}")
    return parsed.scheme, parts


def parse_resource_uri(uri: str) -> ResourceUri:
    scheme, parts = _normalize_resource_parts(uri)
    if scheme == "skill" and not parts:
        raise ValueError(f"Skill resource URI must include a skill name: {uri}")
    if scheme == "skill" and len(parts) == 1:
        parts = [parts[0], "SKILL.md"]
    return ResourceUri(scheme=scheme, value=Path(*parts).as_posix())


def resolve_resource_uri(
    uri: str,
    *,
    thread_id: str,
    skills_dir: Path,
    thread_base_dir: Path | None = None,
) -> Path:
    resource = parse_resource_uri(uri)
    thread_paths = ThreadPaths(thread_id=thread_id, base_dir=thread_base_dir)

    if resource.scheme == "skill":
        root = skills_dir.resolve()
    elif resource.scheme == "upload":
        root = thread_paths.uploads_dir.resolve()
    elif resource.scheme == "workspace":
        root = thread_paths.workspace_dir.resolve()
    elif resource.scheme == "output":
        root = thread_paths.outputs_dir.resolve()
    elif resource.scheme == "memory":
        root = thread_paths.memory_dir.resolve()
    else:
        raise ValueError(f"Unsupported resource URI scheme: {resource.scheme}")

    resolved_path = (root / resource.value).resolve()
    try:
        resolved_path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Resource URI resolved outside allowed root: {uri}") from exc
    return resolved_path
