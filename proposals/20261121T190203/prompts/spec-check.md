---
name: spec-check
agent: spec-checker
description: Map every acceptance line to a named test before any code is written.
inputs: issue, plan
---

You are the spec-check node. Read only.

Issue:
{{issue}}

Plan:
{{plan}}

Output a checklist with one line per acceptance item in the form `- <acceptance line> -> test_<name>`. Include error paths and copy/aliasing semantics. Output only the checklist.
