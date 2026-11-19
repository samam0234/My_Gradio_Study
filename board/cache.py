"""목록 조회 결과를 잠시 기억하고, 글이 바뀌면 통째로 버린다."""

from __future__ import annotations

import time


class ListCache:
    def __init__(self) -> None:
        self.generation = 0
        self._items: dict = {}

    def get(self, key: tuple):
        found = self._items.get(key)
        if found is None:
            return None
        generation, value = found
        if generation != self.generation:
            return None
        return value

    def put(self, key: tuple, value) -> None:
        self._items[key] = (self.generation, value)

    def invalidate(self) -> None:
        self.generation += 1


def cached_list(gateway, cache: ListCache, q: str, page: int = 1):
    key = (q or "", page, 10, "-createdAt")
    found = cache.get(key)
    started = time.perf_counter()
    if found is not None:
        elapsed = (time.perf_counter() - started) * 1000
        return found[0], found[1], elapsed, True
    rows, caption = _call(gateway, q, page)
    cache.put(key, (rows, caption))
    elapsed = (time.perf_counter() - started) * 1000
    return rows, caption, elapsed, False


def _call(gateway, q: str, page: int):
    from board.present import search_table

    return search_table(gateway, q, page)
