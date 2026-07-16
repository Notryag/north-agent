from __future__ import annotations

from pathlib import Path

from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from ...threads import ThreadPaths
from .._runtime import resolve_runtime_path, resolve_thread_id

THREAD_RESOURCE_DOMAINS = ("upload", "workspace", "output", "memory")


def _domain_root(paths: ThreadPaths, domain: str) -> Path:
    if domain == "upload":
        return paths.uploads_dir
    if domain == "workspace":
        return paths.workspace_dir
    if domain == "output":
        return paths.outputs_dir
    if domain == "memory":
        return paths.memory_dir
    raise ValueError(f"Unsupported file domain: {domain}")


def list_thread_file_uris(
    *,
    thread_id: str,
    domain: str = "all",
    base_dir: Path | None = None,
) -> list[str]:
    """List readable resource URIs in the current thread directories."""
    normalized_domain = domain.strip().lower()
    domains = THREAD_RESOURCE_DOMAINS if normalized_domain == "all" else (normalized_domain,)
    invalid_domains = [item for item in domains if item not in THREAD_RESOURCE_DOMAINS]
    if invalid_domains:
        raise ValueError(f"Unsupported file domain: {', '.join(invalid_domains)}")

    if base_dir is None:
        raise RuntimeError("File listing requires an explicit base_dir")
    thread_paths = ThreadPaths(thread_id=thread_id, base_dir=base_dir).ensure()
    uris: list[str] = []
    for item_domain in domains:
        root = _domain_root(thread_paths, item_domain)
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(root).as_posix()
            uris.append(f"{item_domain}://{relative_path}")
    return uris


def format_file_listing(uris: list[str]) -> str:
    if not uris:
        return "No files found."
    return "\n".join(["Files:", *(f"- {uri}" for uri in uris)])


@tool
def list_files(
    *,
    runtime: ToolRuntime,
    domain: str = "all",
) -> str:
    """List files available in the current thread as resource URIs for read_file."""
    try:
        uris = list_thread_file_uris(
            thread_id=resolve_thread_id(None, runtime),
            domain=domain,
            base_dir=resolve_runtime_path("thread_base_dir", runtime),
        )
    except Exception as exc:
        return f"List files failed: {exc}"
    return format_file_listing(uris)
