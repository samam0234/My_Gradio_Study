"""공통 API 스펙 v1의 오류 본문."""

from __future__ import annotations

import uuid


def error_body(code: str, message: str, fields: dict | None = None, request_id: str | None = None) -> dict:
    body = {
        "error": {
            "code": code,
            "message": message,
            "requestId": request_id or str(uuid.uuid4()),
        }
    }
    if fields:
        body["error"]["fields"] = fields
    return body


def format_error(status: int, payload: dict | None) -> str:
    error = (payload or {}).get("error") or {}
    lines = [f"{status} {error.get('code', 'ERROR')}: {error.get('message', '요청을 처리하지 못했습니다.')}"]
    for key, messages in (error.get("fields") or {}).items():
        joined = ", ".join(messages) if isinstance(messages, list) else str(messages)
        lines.append(f"{key}: {joined}")
    return "\n".join(lines)
