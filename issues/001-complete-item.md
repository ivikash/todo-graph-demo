# Issue 001: mark an item complete

Add `TodoStore.complete(item_id)`.

Acceptance:
- Marks the item's `done` flag true and returns the updated item.
- Raises `KeyError` when `item_id` does not exist.
- Calling it twice is harmless (stays done, no error).
- Covered by tests in `test_todo.py`.
