from __future__ import annotations

import argparse

from .client import AppClient
from .config import AppConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the DeerFlow-lite demo app.")
    parser.add_argument("message", nargs="?", default="用一句话解释什么是 DeerFlow")
    parser.add_argument("--thread-id", dest="thread_id")
    parser.add_argument("--stream", action="store_true", help="Print AI message chunks as they stream.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = AppConfig.from_env()
    config.validate()
    client = AppClient(config)

    if args.stream:
        for event in client.stream(args.message, thread_id=args.thread_id):
            if event.type == "ai":
                print(event.data["content"])
        return 0

    print(client.chat(args.message, thread_id=args.thread_id))
    return 0
