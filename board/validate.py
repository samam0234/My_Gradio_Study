"""입력 검증. 실패하면 필드 이름과 메시지 목록을 돌려준다."""

from __future__ import annotations


def _add(fields: dict, key: str, message: str) -> None:
    fields.setdefault(key, []).append(message)


def validate_signup(email: str, password: str, nickname: str) -> dict:
    fields: dict = {}
    email = (email or "").strip()
    nickname = (nickname or "").strip()
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        _add(fields, "email", "이메일 형식으로 입력하세요.")
    if len(password or "") < 8:
        _add(fields, "password", "8자 이상 입력하세요.")
    if not nickname or len(nickname) > 30:
        _add(fields, "nickname", "1~30자로 입력하세요.")
    return fields


def validate_post(title: str, body: str, tags: list[str] | None) -> dict:
    fields: dict = {}
    title = title or ""
    body = body or ""
    if not title.strip() or len(title.strip()) > 200:
        _add(fields, "title", "1~200자로 입력하세요.")
    if not body.strip() or len(body) > 5000:
        _add(fields, "body", "1~5000자로 입력하세요.")
    clean = [str(tag).strip() for tag in (tags or []) if str(tag).strip()]
    if len(clean) > 5:
        _add(fields, "tags", "태그는 5개까지입니다.")
    if any(len(tag) > 20 for tag in clean):
        _add(fields, "tags", "태그 하나는 20자까지입니다.")
    return fields


def parse_tags(raw: str) -> list[str]:
    return [part.strip() for part in (raw or "").split(",") if part.strip()]
