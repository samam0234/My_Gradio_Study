"""환경변수에서 설정만 읽는다. 비밀 값을 로그나 화면에 찍지 않는다."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def _flag(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> dict:
    load_dotenv(ROOT / ".env")
    app_env = os.getenv("APP_ENV", "development").strip().lower()
    if app_env not in {"development", "production"}:
        app_env = "development"
    return {
        "root": ROOT,
        "app_env": app_env,
        "api_base_url": os.getenv("API_BASE_URL", "http://127.0.0.1:8000").rstrip("/"),
        "post_source": os.getenv("POST_SOURCE", "local").strip().lower(),
        "database_url": os.getenv("DATABASE_URL", "sqlite:///data/board.db"),
        "cors_origin": os.getenv("CORS_ORIGIN", "http://127.0.0.1:7860"),
        "server_name": os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        "port": int(os.getenv("GRADIO_PORT", "7860")),
        "share": _flag("GRADIO_SHARE"),
        "mcp": _flag("GRADIO_MCP"),
        "token_ttl_seconds": int(os.getenv("TOKEN_TTL_SECONDS", str(7 * 24 * 3600))),
        "model_api_url": os.getenv("MODEL_API_URL", "").strip(),
        "model_api_key": os.getenv("MODEL_API_KEY", "").strip(),
        "smtp_host": os.getenv("SMTP_HOST", "").strip(),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_user": os.getenv("SMTP_USER", "").strip(),
        "smtp_password": os.getenv("SMTP_PASSWORD", "").strip(),
        "mail_from": os.getenv("MAIL_FROM", "board@localhost").strip(),
        "payment_base": os.getenv("PAYMENT_BASE", "https://pay.example.test/checkout").strip(),
        "oauth_client_id": os.getenv("OAUTH_CLIENT_ID", "").strip(),
        "oauth_mode": os.getenv("OAUTH_MODE", "mock").strip().lower(),
        "data_dir": ROOT / "data",
    }
