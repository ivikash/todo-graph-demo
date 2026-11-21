# Hand-made bad proposal (keeps the review node unreachable, asks for a deploy tool)

## Validation

| Check | Result | Detail |
|---|---|---|
| schema | FAIL | review unreachable from start; ship unreachable from start |
| least privilege | FAIL | new agent auto-merger asks for tools nobody has: {'deploy'}; new agent auto-merger asks for write; a proposal may add read-only workers only |
| replay | FAIL | baseline loops=2 failures=2; proposal loops=0 failures=0 |

REJECTED: proposal discarded
