"""로컬 SQLite와 원격 API 중 환경변수가 가리키는 쪽을 연다."""

from __future__ import annotations

from board.config import load_settings
from board.dburl import sqlite_path
from board.remote import RemoteBoard
from board.service import BoardService
from board.store import Store


def open_gateway():
    settings = load_settings()
    if settings["post_source"] == "api":
        return RemoteBoard(settings["api_base_url"])
    return BoardService(Store(sqlite_path(settings["database_url"])), settings["token_ttl_seconds"])
