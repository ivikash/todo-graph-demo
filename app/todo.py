"""A tiny in-memory to-do store. The graph of agents maintains this file."""


class TodoStore:
    def __init__(self):
        self._items = {}
        self._next_id = 1

    def add(self, title: str) -> dict:
        if not title or not title.strip():
            raise ValueError("title must not be empty")
        item = {"id": self._next_id, "title": title.strip(), "done": False}
        self._items[item["id"]] = item
        self._next_id += 1
        return item

    def list(self) -> list:
        return [dict(i) for i in self._items.values()]
