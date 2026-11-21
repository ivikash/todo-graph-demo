# Lessons

Written by the `learn` node after any run that needed a fix loop or a review rejection.
Read by the `plan`, `build` and `fix` nodes at the start of every run.
Read by the gardener to decide which lesson deserves to become structure (a node, an agent, a check) instead of prose.

| Date | Tag | What went wrong | Rule |
|---|---|---|---|
| 2026-11-21 | missing-error-path | Implemented the happy path and skipped the 'raises when missing' acceptance line. | Before building, list every acceptance line that names an exception and write its test first. |
| 2026-11-21 | untested-acceptance-line | One acceptance line shipped without a test and only the reviewer caught it. | Map every acceptance line to a named test before writing code. |
