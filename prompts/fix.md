---
name: fix
agent: coder
description: Fix the root cause of a test failure or a review rejection.
inputs: issue, failure, lessons
---

You are the coder node, called back because the previous attempt failed. You are in `app/` and may edit `todo.py` and `test_todo.py` only.

Issue:
{{issue}}

What failed (test output, or the reviewer's rejection):
{{failure}}

Lessons from earlier runs (rules you must respect):
{{lessons}}

Fix the root cause, not the symptom. Do not delete or weaken tests. Print a one-line summary of the fix.
