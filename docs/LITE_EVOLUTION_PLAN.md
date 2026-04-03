# Deerflow Lite Evolution Plan

## Goal

Evolve the current minimal `create_agent()` demo into a compact DeerFlow-like runtime with:

- small code size
- stable public API
- multi-turn capability
- useful tool support
- practical runtime safety

This plan is intentionally staged. Each phase should produce a usable system.

## Principles

1. Keep `AppClient.chat()` and `AppClient.stream()` stable.
2. Add one layer of abstraction only when it unlocks multiple future features.
3. Prefer state, tool, and middleware additions over broad framework work.
4. Stop before the codebase turns into a partial clone of full DeerFlow.

## Phase 0: Stabilize The Current Baseline

### Objective

Clean the minimal app so it is a proper foundation.

### Changes

1. Remove debug output from `app/client.py`
2. Pass `context={"thread_id": thread_id}` into agent execution
3. Normalize stream event shape
4. Add tests for current `chat()` and `stream()` behavior

### Deliverable

A minimal app with:

- no debug leftovers
- reproducible stream behavior
- explicit thread context propagation

### Why first

Without this, every later feature gets built on unstable runtime behavior.

## Phase 1: Introduce Runtime Assembly

### Objective

Create one place where runtime dependencies are wired.

### Changes

1. Add `app/runtime.py`
2. Move tool resolution into runtime assembly
3. Move middleware resolution into runtime assembly
4. Move checkpointer resolution into runtime assembly
5. Update `build_agent(...)` to consume runtime outputs

### Suggested API

```python
def get_tools(config: AppConfig) -> list: ...
def get_middlewares(config: AppConfig) -> list: ...
def get_checkpointer(config: AppConfig): ...
def get_state_schema(): ...
```

### Deliverable

Agent construction becomes centralized and future-proof.

### Why second

This is the highest-leverage change. It keeps the project compact while making growth manageable.

## Phase 2: Add Real Thread Runtime

### Objective

Move from a single-turn demo into a thread-aware runtime.

### Changes

1. Expand `ThreadState`
   - `title: str | None`
   - `artifacts: list[str]`
   - `thread_data: dict | None`
   - `uploaded_files: list[dict] | None`
2. Add `app/checkpointer.py`
3. Support default in-memory checkpointing
4. Optionally add sqlite checkpointer later

### Deliverable

The same `thread_id` can carry real conversation state across turns.

### Why here

Thread continuity is one of the core differences between a demo agent and a runtime.

## Phase 3: Add Minimal High-Value Middleware

### Objective

Add only the middleware that gives strong runtime value.

### Changes

1. Add `ToolErrorHandlingMiddleware`
   - convert tool exceptions into `ToolMessage`
2. Add `LoopDetectionMiddleware`
   - prevent repetitive tool call loops
3. Add `ClarificationMiddleware`
   - allow controlled interruption for missing information

### Deliverable

A runtime that is much safer and more controllable under real tasks.

### Why here

These middlewares solve high-frequency failure modes with relatively small code.

## Phase 4: Add Minimal Tooling

### Objective

Support a very small but meaningful tool layer.

### Changes

1. Add tool registry
2. Add `ask_clarification`
3. Add `present_files`
4. Add one simple verification tool
   - example: `get_time`
   - or a local file read tool if needed

### Deliverable

The agent can:

- ask for missing input
- produce presentable file outputs
- prove tool calling works

### Why here

Tooling matters, but tool infrastructure without runtime safety is premature.

## Phase 5: Add Thread File Model

### Objective

Add the smallest useful file/output contract.

### Changes

1. Add `ThreadDataMiddleware`
2. Create thread-local directories
   - `workspace`
   - `uploads`
   - `outputs`
3. Add `app/threads/paths.py`
4. Add `UploadsMiddleware`
   - inject uploaded file information into the last user message

### Deliverable

The runtime can now support:

- per-thread filesystem context
- outputs/artifact presentation
- future upload workflows

### Why here

This is the smallest step that makes the runtime feel product-like rather than purely conversational.

## Phase 6: Tighten The Event Contract

### Objective

Make `stream()` usable by both CLI and a future UI.

### Changes

1. Standardize event types
   - `ai`
   - `tool`
   - `values`
   - `end`
   - `error`
2. Include tool call and tool result events
3. Include final usage or run summary if available

### Deliverable

A front-end friendly runtime stream without needing to redesign the API later.

### Why here

By this point the runtime has enough internal features that the event protocol becomes important.

## Phase 7: Optional Compact Enhancements

These are optional. Only add them if your actual use cases justify them.

### Option A: Auto Title

Add a small title middleware only if you need thread listing or UI display.

### Option B: Basic File Upload API

Only if you actually have a UI or external client that uploads files.

### Option C: SQLite Persistence

Only if multi-process or restart persistence is required.

### Option D: Small Subagent Layer

Only if you already have tasks that clearly benefit from delegation.

Do not add memory, sandbox, MCP, or subagent support by default.

## Recommended Implementation Order

Use this exact order:

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6

This order minimizes rework.

## What To Avoid

### Avoid 1

Do not add many tools before you add tool error handling and loop control.

### Avoid 2

Do not implement many state fields before a concrete feature needs them.

### Avoid 3

Do not let CLI needs shape the internal runtime too much. CLI should remain a thin shell.

### Avoid 4

Do not import full DeerFlow complexity like sandbox, memory, or MCP too early.

### Avoid 5

Do not turn `AppClient` into a place that knows about tools, filesystem paths, and persistence all at once.

## Success Criteria By Stage

### After Phase 1

- agent assembly is centralized
- the public API remains unchanged

### After Phase 2

- repeated `thread_id` supports multi-turn state

### After Phase 3

- tool failures do not crash the whole run
- tool loops are bounded
- clarification can stop a run cleanly

### After Phase 4

- the runtime supports a meaningful but small tool set

### After Phase 5

- thread-local file and artifact flows exist

### After Phase 6

- the stream API is stable enough for UI integration

## Proposed Near-Term Tasks

The next concrete implementation tasks should be:

1. Remove debug print and pass runtime context in `app/client.py`
2. Add `app/runtime.py` and route `build_agent(...)` through it
3. Add `app/checkpointer.py` with in-memory default
4. Expand `ThreadState` for `artifacts` and `thread_data`
5. Add `ToolErrorHandlingMiddleware`
6. Add `LoopDetectionMiddleware`

That set gives the best cost-to-value ratio.

## Final Recommendation

Your lite version should stop when it reaches:

- checkpointed thread state
- small tool registry
- 3 to 5 focused middleware
- artifact/file presentation
- stable event stream

At that point it will cover most of the practical value of DeerFlow while staying compact.
