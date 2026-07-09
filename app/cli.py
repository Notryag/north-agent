from __future__ import annotations

import argparse

from north.client import AppClient, StreamEvent
from north.config import AppConfig


def format_stream_event(event: StreamEvent) -> str:
    if event.type == "tool":
        name = event.data.get("name") or "<unknown>"
        status = event.data.get("status") or "success"
        content = event.data.get("content") or ""
        header = f"[tool:{name}] {status}"
        return f"{header}\n{content}" if content else header

    if event.type == "values":
        artifacts = event.data.get("artifacts")
        if isinstance(artifacts, tuple) and artifacts:
            return f"[values] artifacts={', '.join(artifacts)}"
        return "[values] state updated"

    if event.type == "error":
        message = event.data.get("message") or ""
        error_type = event.data.get("error_type") or "Error"
        return f"[error:{error_type}] {message}"

    return ""


def format_artifacts(artifacts: tuple[str, ...]) -> str:
    if not artifacts:
        return ""
    return "\n".join(["Artifacts:", *(f"- {artifact}" for artifact in artifacts)])


def print_artifacts(artifacts: tuple[str, ...]) -> None:
    formatted_artifacts = format_artifacts(artifacts)
    if formatted_artifacts:
        print(formatted_artifacts)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the DeerFlow-lite demo app.")
    parser.add_argument("message", nargs="?", default="用一句话解释什么是 DeerFlow")
    parser.add_argument("--thread-id", dest="thread_id")
    parser.add_argument("--stream", action="store_true", help="Print AI message chunks as they stream.")
    parser.add_argument(
        "--show-events",
        action="store_true",
        help="With --stream, print tool events and state update summaries.",
    )
    parser.add_argument(
        "--skill",
        dest="skills",
        action="append",
        default=None,
        help="Enable a skill by name. Repeat to combine multiple skills.",
    )
    parser.add_argument(
        "--file",
        dest="files",
        action="append",
        default=None,
        help="Upload a local UTF-8 text file into the thread before running. Repeat to upload multiple files.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = AppConfig.from_env()
    config.validate()
    client = AppClient(config)

    if args.stream:
        artifacts: tuple[str, ...] = ()
        for event in client.stream(args.message, thread_id=args.thread_id, skills=args.skills, files=args.files):
            if event.type == "ai":
                print(event.data["content"])
            elif args.show_events:
                formatted_event = format_stream_event(event)
                if formatted_event:
                    print(formatted_event)
            event_artifacts = event.data.get("artifacts")
            if isinstance(event_artifacts, tuple):
                artifacts = event_artifacts
        print_artifacts(artifacts)
        return 0

    response = client.chat(args.message, thread_id=args.thread_id, skills=args.skills, files=args.files)
    print(response)
    print_artifacts(response.artifacts)
    return 0
