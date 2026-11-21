---
name: todo-graph-instructions
kind: instructions
harness: claude-code
description: Standing rules for an agent working in this checkout, read at session start.
---

# To-do graph: Claude Code edition

You maintain `app/todo.py` through a graph of subagents, not by hand. The graph is the `run-issue` skill. Hooks run the tests after every edit and refuse to let you stop while red; you do not need to be told to verify.

## Self-improvement loop (runs every session)

1. At session start, read `lessons.md`. Every row is a rule for this session.
2. After any correction from the user, or any run that needed a fix pass, add one row to `lessons.md`: date, tag, what went wrong, the rule that prevents it.
3. When a tag appears twice, do not write a third rule. Run the `gardener` skill so the rule becomes a node in the graph.
4. Never mark an issue done without `scripts/verify.sh` exit 0 and a `VERDICT: PASS` from the reviewer subagent.

## Delegation

- `planner`, `coder`, `reviewer`, `scribe` are subagents under `.claude/agents/`. Use them by name; do not do their work in the main thread.
- The reviewer gets the issue and the diff only. Never paste the plan or your notes into its prompt.

## Scope

Edit `app/` through the coder only. Never edit `lessons.md` mid-run, `scripts/`, or anything under `.claude/` unless the gardener's proposal was applied by the user.
