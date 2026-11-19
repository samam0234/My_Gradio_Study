"""같은 토큰의 글 작성이 겹치면 두 번째 호출을 거절한다."""

from __future__ import annotations

import threading

_guards: dict[str, threading.Lock] = {}
_meta = threading.Lock()


def try_lock(key: str) -> threading.Lock | None:
    with _meta:
        guard = _guards.setdefault(key or "anonymous", threading.Lock())
    if not guard.acquire(blocking=False):
        return None
    return guard
