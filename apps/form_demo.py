"""study5. 검증 메시지와 중복 제출 거절."""

from __future__ import annotations

import gradio as gr

from board.gateway import open_gateway
from board.present import create_message, login_session


def build() -> gr.Blocks:
    gateway = open_gateway()

    def submit(email: str, password: str, title: str, body: str):
        try:
            token, hello = login_session(gateway, email, password)
            created = create_message(gateway, token, title, body, "form")
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc
        return f"{hello}\n{created}"

    with gr.Blocks(title="입력 검증", analytics_enabled=False) as demo:
        gr.Markdown("# 로그인 후 글 작성")
        gr.Markdown("비어 있는 제목은 400이고, 필드 문장이 오류 창에 올라온다. 처리 중 같은 로그인으로 다시 누르면 429이다.")
        email = gr.Textbox(label="이메일", value="mina@example.com")
        password = gr.Textbox(label="비밀번호", type="password", value="password123")
        title = gr.Textbox(label="제목")
        body = gr.Textbox(label="본문", lines=4)
        result = gr.Textbox(label="결과")
        gr.Button("제출", variant="primary").click(
            submit,
            inputs=[email, password, title, body],
            outputs=result,
            concurrency_limit=1,
            api_name="submit_post",
        )
    return demo
