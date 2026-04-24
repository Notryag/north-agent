---
name: writer
description: Markdown report writing workflow for thread output artifacts.
tools:
  - write_report
  - present_files
---

Use this skill when the user asks to draft, polish, or package a Markdown report.

Workflow:

1. Produce Markdown that can stand alone as a saved artifact.
2. Use clear headings and short sections.
3. Preserve source links or evidence notes supplied earlier in the thread.
4. Write the report with `write_report`.
5. Call `present_files` with the report filename so the artifact appears in the thread state.

Default filename:

- Use `report.md` unless the user requests a different name.
