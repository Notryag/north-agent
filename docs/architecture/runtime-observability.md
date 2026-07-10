# Runtime Observability

`north` follows DeerFlow's separation between live transport, durable event storage,
and product presentation without copying the DeerFlow Gateway into the harness.

## Boundaries

- `RuntimeJournal` translates LangChain callbacks into product-neutral events.
- `RuntimeEventSink` is an async integration boundary owned by the caller.
- `north` does not choose a database, SSE server, tenant policy, or user-facing text.
- Product applications sanitize and persist events, then project them into their UI.
- Live stream fanout and durable history are separate concerns. A live stream may be
  Redis-backed while the durable source of truth remains PostgreSQL.

## Event Contract

The initial contract covers:

- `model.started`, `model.completed`, `model.error`
- `tool.started`, `tool.completed`, `tool.error`

Model events include a call ID, caller classification, latency, and usage metadata.
Tool events include a call ID, tool name, inputs or output, latency, and errors. Call
IDs let products correlate a tool start with its terminal event.

## Security

The journal does not persist model prompts. Event payloads can still contain sensitive
tool arguments or results, so every product sink must apply an allowlist before storage
or display. Raw provider reasoning is not synthesized by `north`; provider-supplied
reasoning may be carried in a model message and products decide whether it is safe to
show.

Never emit credentials, system prompts, database connection strings, hidden tenant
context, or unrestricted tool output to a user-facing stream.

## Invocation

`invoke_agent_once(..., event_sink=...)` appends a `RuntimeJournal` to existing runnable
callbacks. With no sink, invocation behavior is unchanged.
