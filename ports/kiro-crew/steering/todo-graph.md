---
name: todo-graph-instructions
kind: instructions
harness: kiro-crew
inclusion: always
description: Standing rules for an agent working in this checkout, read at session start.
---

# To-do graph: Kiro Crew edition (steering)

You maintain `app/todo.py` through a graph of agents, not by hand. The graph is the `run-issue` skill. Where the skill says "delegate to `<agent>`", call `spawn_run` with `agent="todo-<agent>"` and only the quoted text as the task. For the reviewer pass `include_memory=false` and `include_lessons=false` so it sees nothing but the issue and the diff.

## Self-improvement loop

1. At the start of a run read `lessons.md`. Every row is a rule for this run.
2. After any correction from the user, or any run that needed a fix pass, do both: append one row to `lessons.md`, and `learn_add` the same rule so it follows you into other sessions.
3. When a tag appears twice in `lessons.md`, do not write a third rule. Run the `gardener` skill so the rule becomes a node in the graph.
4. Never report an issue done without `scripts/verify.sh` exit 0 and a `VERDICT: PASS` from `todo-reviewer`.

## Schedules

- Nightly gardener: one `cron_add` job with the message "Use the gardener skill on this project. Propose at most one change, run scripts/validate_proposal.py, do not apply. Report the proposal folder." (`persistent_session=false`, `hide_in_chat=true`).
- Optional issue sweep: a cron that runs the run-issue skill on every file in `issues/` without a matching line in `runs.log`.

## Scope

Edit `app/` through `todo-coder` only. Never edit `lessons.md` mid-run, `scripts/`, or the agent JSONs unless the gardener's proposal was applied by the user.
