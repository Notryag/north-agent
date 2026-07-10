import asyncio

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage

from north import CompactionEvent, NorthSummarizationMiddleware


class SummaryModel:
    async def ainvoke(self, prompt, config=None):
        del prompt, config
        return AIMessage(content="用户正在安排发布会议，尚未确定参会人。")


def test_async_compaction_preserves_recent_messages_and_calls_hook() -> None:
    events: list[CompactionEvent] = []

    async def record(event: CompactionEvent) -> None:
        events.append(event)

    middleware = NorthSummarizationMiddleware(
        model=SummaryModel(),
        trigger=("messages", 5),
        keep=("messages", 2),
        token_counter=lambda messages: len(list(messages)),
        compaction_hooks=[record],
    )
    messages = [
        HumanMessage(content="安排发布会"),
        AIMessage(content="什么时候？"),
        HumanMessage(content="明天下午"),
        AIMessage(content="参会人呢？"),
        HumanMessage(content="还没确定"),
    ]

    update = asyncio.run(middleware.abefore_model({"messages": messages}, None))

    assert update is not None
    assert update["summary_text"] == "用户正在安排发布会议，尚未确定参会人。"
    assert isinstance(update["messages"][0], RemoveMessage)
    assert update["messages"][-2:] == messages[-2:]
    assert len(events) == 1
    assert events[0].summarized_messages == tuple(messages[:3])
    assert events[0].preserved_messages == tuple(messages[-2:])
