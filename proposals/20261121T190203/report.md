# Proposal from gardener (20261121T190203)

Evidence: 3 runs, 2 fix loops total, most frequent lesson tag `untested-acceptance-line` x1.

Change: new agent `spec-checker` (tools ['read']) and new node `spec-check` between `plan` and `build`.
Why: map every acceptance line to a named test before any code is written.

## Validation

| Check | Result | Detail |
|---|---|---|
| schema | PASS | start reachable, every edge resolves, every node reachable |
| least privilege | PASS | no agent gained tools, new agents read-only |
| replay | PASS | baseline loops=2 failures=2; proposal loops=0 failures=0 |

VALIDATED: safe to apply (human step)
