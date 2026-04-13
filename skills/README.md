# Skills

本目录用于放本地 skill 定义。

最小目录结构：

```text
skills/
└── research/
    ├── skill.json
    └── prompt.md
```

`skill.json` 示例：

```json
{
  "name": "research",
  "description": "Web research workflow",
  "tools": ["web_search", "web_fetch", "write_report", "present_files"]
}
```

说明：

- `prompt.md` 可选；存在时会被拼进最终 `system_prompt`
- `tools` 可选；省略时不限制工具，填写后会按名称过滤工具集合
- 通过 `.env` 中的 `APP_SKILLS` 或 CLI 的 `--skill` 启用
