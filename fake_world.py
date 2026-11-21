"""Deterministic stand-ins for the LLM nodes, so the graph mechanics (fix loops,
review rejections, lessons, gardener replay) can be watched without spending tokens.

The fake coder makes one realistic mistake per issue on its first attempt:
  001: happy path only, forgets the KeyError path       -> tests fail  -> fix loop
  002: gets it right first time                         -> clean run
  003: implementation right, one acceptance line untested -> reviewer rejects -> fix loop
If the graph has run a `spec-check` node before build (the gardener's proposal),
the coder has the acceptance->test checklist in hand and gets 001/003 right first time.
"""
import re
from pathlib import Path

COMPLETE_BUGGY = '''
    def complete(self, item_id: int) -> dict:
        item = self._items.get(item_id)
        if item is not None:
            item["done"] = True
        return item
'''
COMPLETE_GOOD = '''
    def complete(self, item_id: int) -> dict:
        item = self._items[item_id]  # KeyError when missing
        item["done"] = True
        return dict(item)
'''
TESTS_001 = '''
    def test_complete_marks_done(self):
        s = TodoStore()
        s.add("a")
        self.assertTrue(s.complete(1)["done"])

    def test_complete_missing_raises(self):
        s = TodoStore()
        with self.assertRaises(KeyError):
            s.complete(42)

    def test_complete_twice_is_harmless(self):
        s = TodoStore()
        s.add("a")
        s.complete(1)
        self.assertTrue(s.complete(1)["done"])
'''
DELETE_GOOD = '''
    def delete(self, item_id: int) -> None:
        del self._items[item_id]
'''
TESTS_002 = '''
    def test_delete_removes(self):
        s = TodoStore()
        s.add("a")
        s.delete(1)
        self.assertEqual(s.list(), [])

    def test_delete_missing_raises(self):
        s = TodoStore()
        with self.assertRaises(KeyError):
            s.delete(7)

    def test_ids_never_reused(self):
        s = TodoStore()
        s.add("a")
        s.delete(1)
        self.assertEqual(s.add("b")["id"], 2)
'''
LIST_OLD = '''    def list(self) -> list:
        return [dict(i) for i in self._items.values()]
'''
LIST_NEW = '''    def list(self, done=None) -> list:
        items = self._items.values()
        if done is not None:
            items = [i for i in items if i["done"] == done]
        return [dict(i) for i in items]
'''
TESTS_003 = '''
    def test_list_all_by_default(self):
        s = TodoStore()
        s.add("a"); s.add("b"); s.complete(1)
        self.assertEqual(len(s.list()), 2)

    def test_list_done_filter(self):
        s = TodoStore()
        s.add("a"); s.add("b"); s.complete(1)
        self.assertEqual([i["id"] for i in s.list(done=True)], [1])
        self.assertEqual([i["id"] for i in s.list(done=False)], [2])
'''
TESTS_003_COPIES = '''
    def test_list_filtered_returns_copies(self):
        s = TodoStore()
        s.add("a")
        s.list(done=False)[0]["title"] = "changed"
        self.assertEqual(s.list()[0]["title"], "a")
'''


def _append_tests(test_path: Path, block: str):
    src = test_path.read_text()
    marker = '\n\nif __name__ == "__main__":'
    src = src.replace(marker, block.rstrip("\n") + "\n" + marker, 1)
    test_path.write_text(src)


def _insert_method(todo_path: Path, block: str):
    todo_path.write_text(todo_path.read_text().rstrip("\n") + "\n" + block)


def fake_llm(node: str, agent: str, state: dict, app: Path) -> str:
    issue_id = state["issue_id"]
    todo, tests = app / "todo.py", app / "test_todo.py"
    careful = state.get("spec_checked", False)

    if node == "plan":
        return "1. Add the method.\n2. One test per acceptance line.\n3. Keep existing tests green."
    if node == "spec-check":
        state["spec_checked"] = True
        return "Checklist: every acceptance line mapped to a test name, including error paths and copy semantics."
    if node == "build":
        if issue_id == "001":
            _insert_method(todo, COMPLETE_GOOD if careful else COMPLETE_BUGGY)
            _append_tests(tests, TESTS_001)
            return "Added complete(); added 3 tests."
        if issue_id == "002":
            _insert_method(todo, DELETE_GOOD)
            _append_tests(tests, TESTS_002)
            return "Added delete(); added 3 tests."
        if issue_id == "003":
            todo.write_text(todo.read_text().replace(LIST_OLD, LIST_NEW))
            _append_tests(tests, TESTS_003 + (TESTS_003_COPIES if careful else ""))
            return "list(done=None) filter; added tests."
        return "nothing to do"
    if node == "fix":
        if issue_id == "001":
            todo.write_text(todo.read_text().replace(COMPLETE_BUGGY, COMPLETE_GOOD))
            return "complete() now raises KeyError for unknown ids and returns a copy."
        if issue_id == "003":
            if "test_list_filtered_returns_copies" not in tests.read_text():
                _append_tests(tests, TESTS_003_COPIES)
            return "Added the missing copy-semantics test."
        return "no-op fix"
    if node == "review":
        if issue_id == "003" and "test_list_filtered_returns_copies" not in tests.read_text():
            return "The 'still returns copies' acceptance line has no test.\nVERDICT: FAIL acceptance line 'still returns copies' is untested"
        return "Every acceptance line has a test, nothing extra.\nVERDICT: PASS"
    if node == "learn":
        if not state["failures"]:
            return "NO LESSON"
        first = state["failures"][0]
        if first["kind"] == "tests":
            return (f"| {state['date']} | missing-error-path | Implemented the happy path and skipped the "
                    f"'raises when missing' acceptance line. | Before building, list every acceptance line "
                    f"that names an exception and write its test first. |")
        return (f"| {state['date']} | untested-acceptance-line | One acceptance line shipped without a test "
                f"and only the reviewer caught it. | Map every acceptance line to a named test before writing code. |")
    return ""
