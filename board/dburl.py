"""DATABASE_URL을 읽고, 이 저장소가 실제로 여는 파일 경로를 정한다."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse

from board.config import ROOT


def describe_database(url: str) -> dict:
    """연결 문자열의 종류만 설명한다. 다른 DB 드라이버가 없어도 호출할 수 있다."""
    text = (url or "").strip()
    if text.startswith("sqlite:"):
        return {
            "dialect": "sqlite",
            "driver": "stdlib sqlite3",
            "server": False,
            "note": "파일 하나라 학습 기본값으로 쓴다. 계정 테이블과 글 테이블을 SQL로 나눈다.",
        }
    if text.startswith("postgres"):
        return {
            "dialect": "postgresql",
            "driver": "psycopg 또는 SQLAlchemy",
            "server": True,
            "note": "서버가 따로 있다. 바인딩은 드라이버마다 다르므로 SQL 문자열에 값을 붙이지 않는다.",
        }
    if text.startswith("mysql") or text.startswith("mariadb"):
        return {
            "dialect": "mariadb",
            "driver": "PyMySQL 또는 SQLAlchemy",
            "server": True,
            "note": "MariaDB와 MySQL 프로토콜은 같다. 문자셋은 utf8mb4로 맞춘다.",
        }
    if text.startswith("mongodb:") or text.startswith("mongodb+srv:"):
        return {
            "dialect": "mongodb",
            "driver": "pymongo",
            "server": True,
            "note": "컬렉션에 문서를 넣는다. 댓글 수는 조인 대신 문서 안 숫자나 집계로 센다.",
        }
    return {
        "dialect": "unknown",
        "driver": "",
        "server": False,
        "note": "sqlite, postgresql, mariadb, mongodb 중 하나의 스킴으로 시작해야 한다.",
    }


def sqlite_path(url: str) -> Path:
    parsed = urlparse(url)
    if parsed.scheme != "sqlite":
        raise ValueError("이 실행 경로는 sqlite URL만 파일로 엽니다.")
    raw = parsed.path or ""
    if raw.startswith("//"):
        return Path(raw[2:] if not raw.startswith("///") else raw[1:])
    if raw.startswith("/"):
        relative = raw.lstrip("/")
        return ROOT / relative
    return ROOT / raw
