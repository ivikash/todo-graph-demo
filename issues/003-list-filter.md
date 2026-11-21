# Issue 003: filter the list by done state

Change `TodoStore.list(done=None)`.

Acceptance:
- `list()` keeps returning every item (backwards compatible).
- `list(done=True)` returns only completed items, `list(done=False)` only open ones.
- Still returns copies, never the stored dicts.
- Covered by tests in `test_todo.py`.
