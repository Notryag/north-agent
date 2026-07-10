import asyncio

import pytest

from north import CheckpointerConfig, make_checkpointer


def test_memory_checkpointer_lives_for_context_scope() -> None:
    async def exercise() -> None:
        async with make_checkpointer() as checkpointer:
            assert checkpointer is not None
            assert type(checkpointer).__name__ == "InMemorySaver"

    asyncio.run(exercise())


def test_database_checkpointers_require_connection_strings() -> None:
    async def exercise(config: CheckpointerConfig) -> None:
        async with make_checkpointer(config):
            pass

    with pytest.raises(ValueError, match="SQLite checkpointer requires"):
        asyncio.run(exercise(CheckpointerConfig(backend="sqlite")))

    with pytest.raises(ValueError, match="PostgreSQL checkpointer requires"):
        asyncio.run(exercise(CheckpointerConfig(backend="postgres")))
