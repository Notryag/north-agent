# Thread Persistence

North follows DeerFlow's separation between product conversations and agent execution state.

## Responsibilities

- The host product owns thread metadata, tenant authorization, visible messages, retention,
  structured pending actions, and conversation search.
- North passes `thread_id` through runnable config and uses a LangGraph checkpointer for graph
  state, interrupts, resumability, and compacted context.
- A run is one execution within a thread. A host must not substitute `run_id` for `thread_id`.
- Checkpoint rows are runtime internals and are not a product chat-history API.

## Checkpointer Lifecycle

`make_checkpointer()` supports `memory`, `sqlite`, and `postgres`. Async server and worker hosts
must enter it once during process startup, inject the yielded saver into every agent built by
that process, and exit it during shutdown. Building a saver for every invocation loses thread
continuity and wastes database connections.

The default remains `memory` for tests and local clients. Production hosts should install the
`north[postgres]` extra and use PostgreSQL.

## Context Compaction

The target design adapts DeerFlow's summarization middleware:

1. Trigger on a configurable message, token, or context-fraction threshold.
2. Preserve recent complete turns and replace older runtime messages with `summary_text`.
3. Run a pre-compaction hook so the host can archive messages removed from graph state.
4. Keep product-specific pending actions in host-owned structured state, never only in a
   natural-language summary.

Compaction changes model context, not the user's visible conversation history.

North exposes this through `AppConfig.summarization_*`, `NorthSummarizationMiddleware`, and
`CompactionHook`. The middleware reuses LangChain's safe cutoff selection, writes the latest
summary to the `summary_text` state channel, retains recent complete message groups, and invokes
host hooks after summary generation. Hook failures are logged and do not fail the agent run.
