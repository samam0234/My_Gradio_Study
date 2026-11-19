"""SQLite에 사용자, 글, 댓글, 토큰 해시를 저장한다."""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    nickname TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    body TEXT NOT NULL,
    author_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tokens (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL
);
"""

_ORDERS = {
    "createdAt": "p.created_at ASC, p.id ASC",
    "-createdAt": "p.created_at DESC, p.id DESC",
    "-commentCount": "comment_count DESC, p.id DESC",
}


def _user(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "email": row["email"],
        "nickname": row["nickname"],
        "passwordHash": row["password_hash"],
        "createdAt": row["created_at"],
    }


def _post(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "body": row["body"],
        "tags": json.loads(row["tags"]),
        "authorId": row["author_id"],
        "authorNickname": row["author_nickname"],
        "commentCount": row["comment_count"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def create_user(self, email: str, password_hash: str, nickname: str, created_at: str) -> dict:
        with self._lock:
            cursor = self._conn.execute(
                "INSERT INTO users (email, password_hash, nickname, created_at) VALUES (?, ?, ?, ?)",
                (email, password_hash, nickname, created_at),
            )
            self._conn.commit()
            user_id = cursor.lastrowid
        found = self.get_user_by_id(user_id)
        if found is None:
            raise RuntimeError("사용자를 저장한 뒤 다시 읽지 못했습니다.")
        return found

    def get_user_by_email(self, email: str) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return _user(row) if row else None

    def get_user_by_id(self, user_id: int) -> dict | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return _user(row) if row else None

    def insert_token(self, token_hash: str, user_id: int, expires_at: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO tokens (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (token_hash, user_id, expires_at),
            )
            self._conn.commit()

    def get_user_by_token_hash(self, token_hash: str, now: str) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                """
                SELECT u.* FROM tokens t
                JOIN users u ON u.id = t.user_id
                WHERE t.token_hash = ? AND t.expires_at > ?
                """,
                (token_hash, now),
            ).fetchone()
        return _user(row) if row else None

    def delete_token_hash(self, token_hash: str) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM tokens WHERE token_hash = ?", (token_hash,))
            self._conn.commit()

    def insert_post(self, title: str, body: str, tags: list[str], author_id: int, now: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                """
                INSERT INTO posts (title, body, tags, author_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (title, body, json.dumps(tags, ensure_ascii=False), author_id, now, now),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def update_post(self, post_id: int, title: str, body: str, tags: list[str], now: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE posts SET title = ?, body = ?, tags = ?, updated_at = ? WHERE id = ?",
                (title, body, json.dumps(tags, ensure_ascii=False), now, post_id),
            )
            self._conn.commit()

    def delete_post(self, post_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
            self._conn.commit()

    def get_post(self, post_id: int) -> dict | None:
        with self._lock:
            row = self._conn.execute(self._select_sql() + " WHERE p.id = ?", (post_id,)).fetchone()
        return _post(row) if row else None

    def count_posts(self, q: str) -> int:
        pattern = f"%{q.casefold()}%"
        with self._lock:
            row = self._conn.execute(
                """
                SELECT COUNT(*) AS n FROM posts p
                WHERE (? = '' OR lower(p.title) LIKE ? OR lower(p.body) LIKE ?)
                """,
                (q, pattern, pattern),
            ).fetchone()
        return int(row["n"])

    def list_posts(self, q: str, limit: int, offset: int, sort: str) -> list[dict]:
        order = _ORDERS.get(sort, _ORDERS["-createdAt"])
        pattern = f"%{q.casefold()}%"
        sql = (
            self._select_sql()
            + " WHERE (? = '' OR lower(p.title) LIKE ? OR lower(p.body) LIKE ?)"
            + f" ORDER BY {order} LIMIT ? OFFSET ?"
        )
        with self._lock:
            rows = self._conn.execute(sql, (q, pattern, pattern, limit, offset)).fetchall()
        return [_post(row) for row in rows]

    def insert_comment(self, post_id: int, body: str, author_id: int, now: str) -> int:
        with self._lock:
            cursor = self._conn.execute(
                "INSERT INTO comments (post_id, body, author_id, created_at) VALUES (?, ?, ?, ?)",
                (post_id, body, author_id, now),
            )
            self._conn.commit()
            return int(cursor.lastrowid)

    def list_comments(self, post_id: int) -> list[dict]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT c.id, c.body, c.created_at, u.id AS author_id, u.nickname
                FROM comments c JOIN users u ON u.id = c.author_id
                WHERE c.post_id = ? ORDER BY c.id ASC
                """,
                (post_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "body": row["body"],
                "createdAt": row["created_at"],
                "author": {"id": row["author_id"], "nickname": row["nickname"]},
            }
            for row in rows
        ]

    def get_comment(self, comment_id: int) -> dict | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT id, post_id, body, author_id, created_at FROM comments WHERE id = ?",
                (comment_id,),
            ).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"],
            "postId": row["post_id"],
            "body": row["body"],
            "authorId": row["author_id"],
            "createdAt": row["created_at"],
        }

    def delete_comment(self, comment_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
            self._conn.commit()

    def _select_sql(self) -> str:
        return """
            SELECT p.id, p.title, p.body, p.tags, p.author_id, p.created_at, p.updated_at,
                   u.nickname AS author_nickname,
                   (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id) AS comment_count
            FROM posts p
            JOIN users u ON u.id = p.author_id
        """
