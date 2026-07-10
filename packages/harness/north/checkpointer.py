from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Literal


CheckpointerBackend = Literal["memory", "sqlite", "postgres"]


@dataclass(frozen=True, slots=True)
class CheckpointerConfig:
    backend: CheckpointerBackend = "memory"
    connection_string: str | None = None


def get_default_checkpointer():
    """Return the process-local fallback used by simple and test clients."""
    from langgraph.checkpoint.memory import InMemorySaver

    return InMemorySaver()


@asynccontextmanager
async def make_checkpointer(
    config: CheckpointerConfig | None = None,
) -> AsyncIterator[object]:
    """Create a checkpointer for an async application's full lifetime."""
    resolved = config or CheckpointerConfig()
    if resolved.backend == "memory":
        yield get_default_checkpointer()
        return

    if resolved.backend == "sqlite":
        if not resolved.connection_string:
            raise ValueError("SQLite checkpointer requires a connection string")
        try:
            from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        except ImportError as exc:
            raise ImportError("SQLite checkpointer requires the 'sqlite' north extra") from exc
        async with AsyncSqliteSaver.from_conn_string(resolved.connection_string) as saver:
            await saver.setup()
            yield saver
        return

    if resolved.backend == "postgres":
        if not resolved.connection_string:
            raise ValueError("PostgreSQL checkpointer requires a connection string")
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
            from psycopg.rows import dict_row
            from psycopg_pool import AsyncConnectionPool
        except ImportError as exc:
            raise ImportError("PostgreSQL checkpointer requires the 'postgres' north extra") from exc
        pool = AsyncConnectionPool(
            resolved.connection_string,
            kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
            check=AsyncConnectionPool.check_connection,
        )
        async with pool:
            saver = AsyncPostgresSaver(conn=pool)
            await saver.setup()
            yield saver
        return

    raise ValueError(f"Unsupported checkpointer backend: {resolved.backend}")
