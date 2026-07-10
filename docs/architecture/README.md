# Architecture Docs

默认不要整读 `architecture/` 下所有文件。

## 最小阅读路径

1. 做具体任务时先看 [TODO](D:/workspace/github/deerflow-lite/docs/TODO.md)
2. 只有当你需要判断模块归属或目录边界时，再看本目录

## 文件分工

- [overview.md](D:/workspace/github/deerflow-lite/docs/architecture/overview.md)
  定位、当前阶段目标、核心能力、任务闭环

- [target-structure.md](D:/workspace/github/deerflow-lite/docs/architecture/target-structure.md)
  目标目录结构，以及每个目录未来负责什么

- [runtime-boundaries.md](D:/workspace/github/deerflow-lite/docs/architecture/runtime-boundaries.md)
  当前模块边界、状态职责、runtime 保护边界、当前阶段不该做的事

- [runtime-observability.md](./runtime-observability.md)
  通用 runtime 事件、产品适配边界与安全约束
