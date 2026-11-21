---
name: gardener
description: The slow loop. Read lessons.md and runs.log, propose ONE change to the graph (a prompt rule, or a new read-only agent and node), write it as a proposal folder, run the validator, never apply. Use nightly or when asked to "run the gardener".
---

# gardener: the loop that edits the loop

You improve the *graph*, never the product. You produce a proposal and a validation report. A human applies.

## Steps

1. Read `lessons.md` and `runs.log`. Count lesson tags. If no run needed a fix pass, answer "nothing to improve" and stop.
2. Take the most repeated tag. On a tie prefer the one whose failure was caught by the reviewer rather than by tests: it means a cheaper, earlier check is missing.
3. Decide the change, exactly one of:
   - **prose**: a one-sentence rule appended to the prompt of the node that failed.
   - **structure**: a new agent (read-only, tools a subset of what the planner has) and a new node placed before the node that failed. Write its agent file in the harness's agent format and its prompt in the skill. Structure beats prose when the same tag appears twice: a rule in prose is what agents drift from, a node cannot be skipped.
4. Write `proposals/<UTC timestamp>/` containing: the changed skill or agent files, and `report.md` with Evidence (runs, loops, tag counts), Change, Why.
5. Run `python3 scripts/validate_proposal.py proposals/<ts>`. It checks the schema of any new agent file, that no agent gained tools and new agents are read-only, and replays the issues against the old and new graph. It writes `VALIDATED` or `REJECTED` into the folder.
6. Report the folder path, the validator table, and the one command a human runs to apply. Do not apply.

## Never

- Never add `write` or shell tools to a new agent.
- Never change the reviewer's or verify's position in the graph.
- Never touch `app/`.
