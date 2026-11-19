"""study14. 스펙 문서와 페이지 이동."""

from __future__ import annotations

import json

import gradio as gr

from board.gateway import open_gateway
from board.openapi_spec import board_openapi
from board.present import search_table


def build() -> gr.Blocks:
    gateway = open_gateway()

    def turn(q: str, page: float):
        try:
            return search_table(gateway, q, int(page or 1))
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    with gr.Blocks(title="API 설계", analytics_enabled=False) as demo:
        gr.Markdown("# 목록 계약")
        gr.Markdown("응답은 `data`와 `meta`다. 오류는 `error.code`, `error.message`, `error.fields`다. 화면 아래 API 문서 버튼은 Gradio가 이벤트마다 만든 호출 문서다.")
        gr.Code(json.dumps(board_openapi(), ensure_ascii=False, indent=2), language="json")
        q = gr.Textbox(label="q")
        page = gr.Number(value=1, label="page", precision=0)
        table = gr.Dataframe(headers=["id", "title"], type="array")
        meta = gr.Textbox(label="meta")
        gr.Button("GET /api/posts").click(turn, inputs=[q, page], outputs=[table, meta], api_name="list_posts")
    return demo
