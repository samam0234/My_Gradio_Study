"""업로드 파일을 새 이름으로 복사한다. 원본 파일명은 저장 경로에 쓰지 않는다."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

MAX_BYTES = 2 * 1024 * 1024
ALLOWED = {".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
IMAGES = {".png", ".jpg", ".jpeg", ".webp"}


def save_upload(source: str | None, dest_dir: Path, *, image_only: bool = False) -> dict:
    if not source:
        return {"saved": False, "name": "", "bytes": 0}
    src = Path(source)
    if not src.is_file():
        raise ValueError("업로드된 파일을 찾지 못했습니다.")
    suffix = src.suffix.lower()
    allowed = IMAGES if image_only else ALLOWED
    if suffix not in allowed:
        raise ValueError("허용되지 않은 파일 형식입니다.")
    size = src.stat().st_size
    if size > MAX_BYTES:
        raise ValueError("413 PAYLOAD_TOO_LARGE: 2MB 이하만 받습니다.")
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex}{suffix}"
    target = dest_dir / name
    shutil.copyfile(src, target)
    return {"saved": True, "name": name, "bytes": size, "kind": "image" if suffix in IMAGES else "file"}
