# DeerFlow Lite 架构说明

这份文件现在只做架构索引。

默认不需要整读整个架构文档体系。

## 什么时候看

- 判断代码应该放哪、模块边界是否清晰：
  看 [runtime-boundaries](D:/workspace/github/deerflow-lite/docs/architecture/runtime-boundaries.md)

- 判断目标目录结构应收敛到哪里：
  看 [target-structure](D:/workspace/github/deerflow-lite/docs/architecture/target-structure.md)

- 判断当前阶段 runtime 到底在逼哪些核心能力：
  看 [overview](D:/workspace/github/deerflow-lite/docs/architecture/overview.md)

- 做具体功能开发：
  优先看 [TODO](D:/workspace/github/deerflow-lite/docs/TODO.md)

## 子文件

- [architecture/README.md](D:/workspace/github/deerflow-lite/docs/architecture/README.md)
  架构子目录索引

- [architecture/overview.md](D:/workspace/github/deerflow-lite/docs/architecture/overview.md)
  定位、当前阶段目标、核心能力、任务闭环

- [architecture/target-structure.md](D:/workspace/github/deerflow-lite/docs/architecture/target-structure.md)
  最终目标目录结构与各目录职责

- [architecture/runtime-boundaries.md](D:/workspace/github/deerflow-lite/docs/architecture/runtime-boundaries.md)
  当前模块边界、状态职责、runtime 保护与不该做的事
