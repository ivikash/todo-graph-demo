# Issue 002: delete an item

Add `TodoStore.delete(item_id)`.

Acceptance:
- Removes the item and returns nothing.
- Raises `KeyError` when `item_id` does not exist.
- Ids are never reused after a delete.
- Covered by tests in `test_todo.py`.
