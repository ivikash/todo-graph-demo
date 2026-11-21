---
name: run-issue
description: Walk the to-do maintenance graph for one issue file. Plan, build, verify, fix loop, fresh-context review, ship, learn. Use when asked to "run issue <path>" or "work issue NNN".
---

# run-issue: the graph, in markdown

This is `graph.json` written for a harness that interprets markdown. Every numbered step is a node. "Delegate to `<agent>`" means spawn that agent as a subagent with ONLY the text under the arrow, so it sees nothing else. The harness's hooks own the hard edges (tests after every edit, no stopping while red); this skill owns the soft ones.

Inputs: the issue file path. Read `lessons.md` first and carry its rules into every delegation.

## Nodes

1. **plan**. Delegate to `planner`:
   > Issue: <issue text>. Lessons: <lessons rows>. Write a numbered plan of at most 6 steps: which function changes, which tests to add (one per acceptance line), and any edge case the acceptance list implies but does not spell out.

2. **build**. Delegate to `coder`:
   > Issue: <issue text>. Plan: <plan>. Lessons: <lessons rows>. Edit `app/todo.py` and `app/test_todo.py` only. Add one test per acceptance line. Do not run the tests, the verify step does that.

3. **verify**. Run `scripts/verify.sh` yourself. Exit 0 goes to step 5. Non-zero goes to step 4 with the output.

4. **fix** (max 3 passes, count them). Delegate to `coder`:
   > Issue: <issue text>. What failed: <test output or reviewer reason>. Lessons: <lessons rows>. Fix the root cause. Do not delete or weaken tests.
   Then back to step 3. On the fourth failure stop and report the run as red.

5. **review**. Delegate to `reviewer` with NO plan, NO build notes and NO memory, only:
   > Issue: <issue text>. Diff: <git diff of app/>. Check every acceptance line has a test, no test was removed or weakened, the implementation matches the issue and nothing more. End with exactly `VERDICT: PASS` or `VERDICT: FAIL <one sentence>`.
   FAIL goes to step 4 with the reason. PASS goes on.

6. **ship**. Run `scripts/verify.sh` once more. Commit `app/` with the issue title as the message.

7. **learn**. Delegate to `scribe`:
   > Issue: <title>. Fix passes: <n>. Failures in order: <list>. If no fix pass and no review rejection answer `NO LESSON`. Otherwise output one row `| <date> | <kebab-tag> | <what went wrong> | <rule, imperative> |`.
   Append the row to `lessons.md`. Append one line to `runs.log`: `<date> <issue> loops=<n> failures=<list of kinds>`.

## Rules the harness cannot see

- A node is a fresh delegation. Never let the reviewer see how the code was built.
- Never answer VERDICT on the reviewer's behalf. If the reviewer did not print a VERDICT line, run step 5 again.
- Lessons are read at the start and written at the end, never edited mid-run.
