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

North applies a Run-aware dual-threshold policy:

1. On the first model call of a Run, compact history above 6,000 approximate tokens or the
   60-message safety ceiling. This normal path runs at most once in that Run.
2. During the Run, compact only when the complete estimated model context exceeds 12,000 tokens.
   The estimate combines message history with the system prompt and initially bound tool schemas.
3. Keep approximately 2,000 tokens of recent history. The safe cutoff never separates an AI
   tool-call batch from its corresponding ToolMessages.
4. Require at least 3,000 newly accumulated history tokens before another compaction and allow at
   most two emergency compactions per Run.
5. Run a pre-compaction hook so the host can archive messages removed from graph state.
6. Keep product-specific pending actions in host-owned structured state, never only in a
   natural-language summary.

Compaction changes model context, not the user's visible conversation history.
JSON-compatible ToolMessage artifacts may carry host presentation data through
the live runtime stream, but the host must persist visible history independently
before a later compaction removes old runtime artifacts.

North exposes this through `AppConfig.summarization_*`, `NorthSummarizationMiddleware`, and
`CompactionHook`. Run counters live in checkpointed `ThreadState`, not mutable middleware fields.
Hosts must pass a stable `run_id` in runtime context; unscoped direct invocations are treated as one
Run and cannot provide per-Run guarantees. The latest summary is written to `summary_text`, and
hook failures are logged without failing the Agent Run.

`history_tokens` is the approximate serialized message history. `context_tokens` adds the fixed
system prompt and initially bound tool schemas calculated during Agent assembly. These metrics are
reported separately on `CompactionEvent`; neither name may be used for the other. Summary model
calls inherit runtime callbacks and carry the `middleware:summarization` tag, so usage remains
auditable even when the host hides internal lifecycle events from end users.

North treats host-defined compact ToolMessage content as opaque. It does not rewrite business
receipts. JSON-compatible presentation artifacts remain attached while their ToolMessage is
retained and may disappear only when that complete message group is compacted; the host is
responsible for durable UI projection before then.
