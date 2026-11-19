"""메일은 기본적으로 보낸편지 JSON으로 남긴다. SMTP_HOST가 있을 때만 실제 발송을 시도한다."""

from __future__ import annotations

import json
import smtplib
from email.message import EmailMessage
from pathlib import Path


def write_outbox(path: Path, recipient: str, subject: str, body: str) -> dict:
    path.parent.mkdir(parents=True, exist_ok=True)
    letter = {"to": recipient, "subject": subject, "body": body}
    path.write_text(json.dumps(letter, ensure_ascii=False, indent=2), encoding="utf-8")
    return letter


def send_or_store(outbox: Path, recipient: str, subject: str, body: str, settings: dict) -> str:
    if not recipient or "@" not in recipient:
        raise ValueError("받는 이메일을 확인하세요.")
    if not subject.strip() or not body.strip():
        raise ValueError("제목과 본문을 입력하세요.")
    host = settings.get("smtp_host") or ""
    if not host:
        write_outbox(outbox, recipient, subject.strip(), body.strip())
        return "SMTP 설정이 없어 보낸편지 파일에 저장했습니다."
    message = EmailMessage()
    message["From"] = settings.get("mail_from") or "board@localhost"
    message["To"] = recipient
    message["Subject"] = subject.strip()
    message.set_content(body.strip())
    with smtplib.SMTP(host, int(settings.get("smtp_port") or 587), timeout=10) as client:
        client.starttls()
        if settings.get("smtp_user"):
            client.login(settings["smtp_user"], settings.get("smtp_password") or "")
        client.send_message(message)
    return "메일을 보냈습니다."
