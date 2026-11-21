# To-do graph: Codex edition

You maintain `app/todo.py` through a graph of subagents, not by hand. The graph is the `run-issue` skill. Hooks run the tests after every `apply_patch` and refuse to let the turn stop while red; you do not need to be told to verify.

## Self-improvement loop (every session)

1. At session start, read `lessons.md`. Every row is a rule for this session.
2. After any correction from the user, or any run that needed a fix pass, add one row to `lessons.md`: date, tag, what went wrong, the rule that prevents it.
3. When a tag appears twice, do not write a third rule. Run the `gardener` skill so the rule becomes a node in the graph.
4. Never report an issue done without `scripts/verify.sh` exit 0 and a `VERDICT: PASS` from the reviewer agent.

## Delegation

- `planner`, `coder`, `reviewer`, `scribe` are custom agents under `.codex/agents/`. When the run-issue skill says "delegate to X", spawn that agent and wait for it; do not do its work on the main thread.
- The reviewer gets the issue and the diff only. Never paste the plan or your notes into its prompt.
- Codex subagents inherit the parent's sandbox, so a read-only agent is read-only by instruction, not by sandbox. The hooks and the validator are what make that hold.

## Scope

Edit `app/` through the coder only. Never edit `lessons.md` mid-run, `scripts/`, or anything under `.codex/` unless the gardener's proposal was applied by the user.
