import unittest

from todo import TodoStore


class TestTodo(unittest.TestCase):
    def test_add_returns_item_with_id(self):
        s = TodoStore()
        item = s.add("buy milk")
        self.assertEqual(item["id"], 1)
        self.assertEqual(item["title"], "buy milk")
        self.assertFalse(item["done"])

    def test_add_rejects_empty_title(self):
        s = TodoStore()
        with self.assertRaises(ValueError):
            s.add("   ")

    def test_list_returns_copies(self):
        s = TodoStore()
        s.add("a")
        items = s.list()
        items[0]["title"] = "changed"
        self.assertEqual(s.list()[0]["title"], "a")


if __name__ == "__main__":
    unittest.main()
