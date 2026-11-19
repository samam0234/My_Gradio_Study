"""파일로 남긴 알림을 읽어 화면에 올린다."""

from __future__ import annotations

from pathlib import Path


def read_notice(path: Path) -> str:
    if not path.exists():
        return "새 알림 없음"
    text = path.read_text(encoding="utf-8").strip()
    return text or "새 알림 없음"


def write_notice(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip(), encoding="utf-8")
