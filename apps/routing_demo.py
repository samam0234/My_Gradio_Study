"""study4. 쿼리 문자열을 읽고, 없는 번호는 오류로 보여 준다."""

from __future__ import annotations

import gradio as gr

from board.gateway import open_gateway
from board.present import post_text, search_table


def build() -> gr.Blocks:
    gateway = open_gateway()

    def from_request(request: gr.Request):
        params = dict(request.query_params) if request else {}
        post_id = params.get("post", "")
        query = params.get("q", "")
        rows, caption = search_table(gateway, query)
        detail = "주소에 post 번호가 없습니다."
        if post_id:
            try:
                detail = post_text(gateway, int(post_id))
            except (ValueError, TypeError) as exc:
                raise gr.Error(str(exc)) from exc
        return query, rows, caption, detail

    def open_post(post_id: float):
        try:
            return post_text(gateway, int(post_id))
        except (ValueError, TypeError) as exc:
            raise gr.Error(str(exc)) from exc

    with gr.Blocks(title="경로", analytics_enabled=False) as demo:
        gr.Markdown("# 쿼리와 오류 화면")
        gr.Markdown("예: `/?q=첫&post=1`. 탭은 화면 나눔이고, 글 번호는 쿼리로 받는다.")
        query = gr.Textbox(label="q")
        table = gr.Dataframe(headers=["id", "title"], datatype=["number", "str"], type="array", label="목록")
        caption = gr.Textbox(label="meta")
        post_id = gr.Number(label="글 번호", precision=0)
        detail = gr.Textbox(label="상세", lines=8)
        gr.Button("이 번호 열기").click(open_post, inputs=post_id, outputs=detail, api_name="open_post")
        demo.load(from_request, outputs=[query, table, caption, detail])
    return demo
