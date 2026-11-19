"""study11. DATABASE_URL의 종류를 읽고, 기본 실행은 SQLite로 목록을 연다."""

from __future__ import annotations

import json

import gradio as gr

from board.config import load_settings
from board.dburl import describe_database
from board.gateway import open_gateway
from board.present import search_table


def build() -> gr.Blocks:
    settings = load_settings()
    info = describe_database(settings["database_url"])
    gateway = open_gateway()

    def show_rows():
        try:
            rows, caption = search_table(gateway, "")
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc
        return rows, caption

    with gr.Blocks(title="DB", analytics_enabled=False) as demo:
        gr.Markdown("# 데이터베이스 연결 문자열")
        gr.Code(json.dumps({"urlKind": info, "postSource": settings["post_source"]}, ensure_ascii=False, indent=2), language="json")
        table = gr.Dataframe(headers=["id", "title"], type="array", label="SQLite 또는 API 목록")
        caption = gr.Textbox(label="목록 정보")
        gr.Button("목록").click(show_rows, outputs=[table, caption])
    return demo
