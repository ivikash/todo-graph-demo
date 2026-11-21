---
name: learn
agent: scribe
description: Write one lessons.md row, or NO LESSON.
inputs: issue_title, loops, failures
---

You are the scribe node. The run below has finished. Read only.

Issue: {{issue_title}}
Fix loops needed: {{loops}}
Failures seen, in order:
{{failures}}

If loops is 0 and there were no review rejections, answer with exactly `NO LESSON`.
Otherwise write ONE lesson as a single markdown table row:
`| <YYYY-MM-DD> | <tag: one kebab-case word for the failure class> | <what went wrong, one sentence> | <the rule that prevents it, one sentence, imperative> |`
Output only that row.
