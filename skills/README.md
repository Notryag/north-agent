# Skills

本目录用于放本地 skill 定义。

最小目录结构：

```text
skills/
└── research/
    └── SKILL.md
```

`SKILL.md` 示例：

```md
---
name: research
description: Web research workflow
tools:
  - web_search
  - web_fetch
  - write_report
  - present_files
---

Focus on traceable sources first, then draft the report.
```

说明：

- agent 默认只看到 skill catalog：`name`、`description`、`location`
- `SKILL.md` 正文不会默认注入；模型需要时通过内置 `read_file` 按路径懒加载
- frontmatter 里的 `tools` 当前只作为 skill 元信息保留，不直接做 runtime tool gating
- 通过 `.env` 中的 `APP_SKILLS` 或 CLI 的 `--skill` 过滤本轮可见 skill
