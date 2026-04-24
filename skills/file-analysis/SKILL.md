---
name: file-analysis
description: Analyze uploaded or thread-local files and produce Markdown reports.
tools:
  - list_files
  - read_file
  - write_report
  - present_files
---

Use this skill when the user asks to inspect, summarize, compare, or report on files.

Workflow:

1. Call `list_files` to discover available thread files.
2. Use `read_file` on the relevant `upload://`, `workspace://`, `output://`, or `memory://` URI.
3. Analyze only the files needed for the user's request.
4. If the user asks for a saved result, write Markdown with `write_report`.
5. Call `present_files` for generated reports so they appear in artifacts.

Boundaries:

- Do not assume access to arbitrary local filesystem paths.
- Prefer resource URIs returned by `list_files`.
- Ask for clarification if the requested file is not present.
