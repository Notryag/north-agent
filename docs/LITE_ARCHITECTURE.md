# Deerflow Lite Architecture

## 1. Purpose

This project should not try to clone full DeerFlow.

The right target is:

- keep the current minimal `create_agent()`-based core
- add only the runtime pieces that create real product value
- preserve a small codebase and stable public API

The architecture should optimize for:

1. low code volume
2. stable extension points
3. usable multi-turn runtime
4. support for most high-value DeerFlow features later

## 2. Current Baseline

The current code already has the correct outer shape:

- `app/config.py`
  runtime config from `.env`
- `app/state.py`
  minimal `ThreadState`
- `app/agent.py`
  central `build_agent(...)`
- `app/client.py`
  `chat()` / `stream()` entry points
- `app/cli.py`
  thin executable shell

That is the correct foundation. The next step is not to add random features, but to turn this into a compact runtime.

## 3. Architecture Goal

The target architecture is:

```text
CLI / Python caller
  -> AppClient
  -> Runtime Provider
  -> build_agent(...)
  -> LangChain agent graph
  -> state + tools + middleware + checkpointer
```

The main design rule:

> The public API stays small, while all future complexity is pushed behind a runtime assembly layer.

## 4. Core Design

### 4.1 Public Surface

Keep the public surface small and stable:

- `AppConfig`
- `AppClient.chat(...)`
- `AppClient.stream(...)`
- `build_agent(...)`

Do not expose internal middleware chains, thread directory logic, or tool registration details to the caller.

### 4.2 Runtime Assembly Layer

Add one central runtime assembly module. This is the most important missing layer.

Recommended new module:

```text
app/runtime.py
```

Responsibilities:

- resolve tools
- resolve middlewares
- resolve checkpointer
- resolve state schema
- build runtime context helpers later

Recommended interface:

```python
class RuntimeProvider:
    def get_tools(self, config: AppConfig) -> list: ...
    def get_middlewares(self, config: AppConfig) -> list: ...
    def get_checkpointer(self, config: AppConfig): ...
    def get_state_schema(self): ...
```

First version can be simple functions instead of a class.

The key is centralization.

### 4.3 State-First Design

The project should evolve around state, not around tools.

Current state:

- only `messages`

Target compact state:

```python
class ThreadState(AgentState):
    title: str | None
    artifacts: list[str]
    thread_data: dict | None
    uploaded_files: list[dict] | None
```

This is enough for a lite runtime.

Do not add memory, todos, viewed images, or large custom reducers yet unless a concrete feature requires them.

### 4.4 Event Protocol

`AppClient.stream()` should become the only runtime event contract.

Recommended lite event types:

- `ai`
- `tool`
- `values`
- `end`
- `error`

Current `message` is acceptable for the first stage, but the target shape should support tools and lifecycle events without changing the caller API later.

Recommended direction:

```python
StreamEvent(type="ai", data={...})
StreamEvent(type="tool", data={...})
StreamEvent(type="values", data={...})
StreamEvent(type="end", data={...})
```

This keeps the client usable by both CLI and future UI.

### 4.5 Checkpointing

Checkpointing should be the first persistence feature.

Rule:

- default to in-memory
- allow optional sqlite later
- keep all persistence behind runtime assembly

Do not wire persistence logic directly into `AppClient`.

### 4.6 Tools

Tool support should be added, but only through one resolver.

Recommended lite split:

```text
app/tools/
├── __init__.py
├── registry.py
├── builtin/
│   ├── clarification.py
│   └── present_files.py
```

Lite runtime should support only a small high-value set:

1. `ask_clarification`
2. `present_files`
3. one demo synchronous tool for verification

Do not build a broad tool marketplace abstraction yet.

### 4.7 Middleware

Middleware should stay minimal and problem-driven.

Recommended lite middlewares:

1. `ToolErrorHandlingMiddleware`
2. `LoopDetectionMiddleware`
3. `ThreadDataMiddleware`
4. `UploadsMiddleware`
5. `ClarificationMiddleware`

This is already enough to cover most practical runtime issues.

Do not add memory, title generation, todo mode, sandbox, vision middleware, or subagent support in the first compact architecture.

## 5. Recommended Target Structure

The target structure should remain small:

```text
app/
├── __init__.py
├── agent.py
├── cli.py
├── client.py
├── config.py
├── runtime.py
├── state.py
├── checkpointer.py
├── middlewares/
│   ├── __init__.py
│   ├── tool_error.py
│   ├── loop_detection.py
│   ├── thread_data.py
│   ├── uploads.py
│   └── clarification.py
├── tools/
│   ├── __init__.py
│   ├── registry.py
│   └── builtin/
│       ├── clarification.py
│       └── present_files.py
└── threads/
    └── paths.py
```

This is still a small codebase, but it creates clean ownership boundaries.

## 6. Module Responsibilities

### `app/config.py`

Owns:

- environment loading
- runtime configuration
- validation

Should not own:

- tool loading
- middleware construction
- filesystem policy

### `app/state.py`

Owns:

- shared state schema
- state reducers if needed

Should remain small.

### `app/runtime.py`

Owns:

- runtime assembly
- dependency resolution for agent creation

This is the strategic module of the lite runtime.

### `app/agent.py`

Owns:

- model creation
- final `create_agent(...)` call

Should not know details of specific tools or middleware wiring beyond consuming runtime provider outputs.

### `app/client.py`

Owns:

- user-facing entry points
- stream event normalization
- `thread_id` handling
- runnable config generation

Should not own:

- filesystem logic
- persistence setup
- tool registration

### `app/checkpointer.py`

Owns:

- in-memory checkpointer creation
- optional sqlite setup later

Keep this isolated so persistence does not leak everywhere.

### `app/middlewares/*`

Own:

- focused runtime behavior only

Each middleware should solve one problem.

### `app/tools/*`

Own:

- tool definitions
- tool discovery / registration

## 7. Data Flow

### 7.1 Chat Flow

```text
caller
  -> AppClient.chat(message, thread_id)
  -> AppClient.stream(...)
  -> build runnable config
  -> get agent from build_agent(...)
  -> agent graph executes
  -> state snapshots streamed back
  -> AppClient converts snapshots to StreamEvent
  -> chat() returns last AI text
```

### 7.2 Future Tool Flow

```text
model
  -> tool_calls
  -> tool execution
  -> ToolMessage
  -> model
  -> final answer
```

### 7.3 Future Clarification Flow

```text
model
  -> ask_clarification
  -> ClarificationMiddleware intercepts
  -> emit structured clarification output
  -> stop current run
```

## 8. What Is Actually Valuable

For this lite codebase, the highest-value architecture pieces are:

1. runtime assembly
2. stable stream event contract
3. checkpointed thread state
4. tool error recovery
5. loop protection
6. thread-local file/output model

Those six items create most of the practical DeerFlow value without requiring the full DeerFlow codebase.

## 9. Design Rules

### Rule 1

Prefer one central extension point over many small ad hoc hooks.

### Rule 2

Add features only when they require a new state field, tool, or middleware.

### Rule 3

Do not let `AppClient` become the place where runtime complexity accumulates.

### Rule 4

Do not add full DeerFlow features unless they pay for themselves in this smaller project.

### Rule 5

Keep the user API unchanged while evolving the runtime internals.

## 10. Immediate Gaps In Current Code

The current implementation is good as a baseline, but these gaps should be fixed before adding many features:

1. `app/client.py` still contains a debug `print(...)`
2. `stream()` does not yet define a future-proof event contract
3. runtime assembly is still implicit
4. state schema is too small for artifacts and thread data
5. checkpointer strategy is not yet formalized

## 11. Final Position

The lite architecture should not aim to be a smaller copy of DeerFlow.

It should aim to be:

- a compact runtime
- with a stable API
- with a deliberate state model
- with a small number of high-value middlewares and tools

That is the shortest path from your current code to a useful simplified DeerFlow.
