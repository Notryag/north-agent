---
name: research
description: Web research workflow for traceable Markdown reports with artifacts.
tools:
  - web_search
  - web_fetch
  - write_report
  - present_files
---

Use this skill when the user asks for web research, current information, source-backed analysis, or a report.

Workflow:

1. Clarify only when the topic, scope, or output requirement is genuinely ambiguous.
2. Search the web with `web_search` using focused queries.
3. Fetch the most relevant sources with `web_fetch`.
4. Synthesize the findings into a concise Markdown report with source URLs near the claims they support.
5. Write the final Markdown with `write_report`, normally as `report.md`.
6. Call `present_files` with the written report path so the runtime records it in thread artifacts.

Report expectations:

- Prefer primary or authoritative sources when available.
- Separate facts from inference.
- Include source URLs in the report body.
- Keep the report scoped to the user's request instead of producing a general survey.
