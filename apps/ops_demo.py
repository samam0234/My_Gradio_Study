"""study16. 실행 중인 앱이 환경과 저장 파일을 스스로 점검한다."""

from __future__ import annotations

import json

import gradio as gr

from board.config import load_settings
from board.dburl import describe_database, sqlite_path


def mount_ops() -> None:
    def report() -> str:
        settings = load_settings()
        path = None
        if settings["database_url"].startswith("sqlite:"):
            path = sqlite_path(settings["database_url"])
        payload = {
            "appEnv": settings["app_env"],
            "port": settings["port"],
            "share": settings["share"],
            "mcp": settings["mcp"],
            "database": describe_database(settings["database_url"]),
            "sqliteExists": bool(path and path.exists()),
            "modelConfigured": bool(settings["model_api_url"]),
            "smtpConfigured": bool(settings["smtp_host"]),
        }
        return json.dumps(payload, ensure_ascii=False, indent=2)

    gr.Markdown("# 배포 후 이 화면으로 환경만 확인한다")
    gr.Markdown("비밀 값 원문은 넣지 않는다. 설정이 있는지만 본다.")
    out = gr.Code(language="json")
    gr.Button("점검").click(report, outputs=out, api_name="ops_report")


def build() -> gr.Blocks:
    with gr.Blocks(title="운영 점검", analytics_enabled=False) as demo:
        mount_ops()
    return demo
