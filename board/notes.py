"""study3에서 쓰는 JSON 파일 저장."""

from __future__ import annotations

import json
from pathlib import Path


def load_notes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def save_note(path: Path, nickname: str, text: str, at: str) -> list[dict]:
    notes = load_notes(path)
    notes.append({"nickname": nickname.strip() or "익명", "text": text.strip(), "at": at})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    return notes
