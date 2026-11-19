"""study2. Blocks로 행, 열, 탭과 클릭 이벤트를 직접 잇는다."""

from __future__ import annotations

import gradio as gr


def shout(message: str) -> tuple[str, str]:
    text = (message or "").strip()
    if not text:
        raise gr.Error("문구를 입력하세요.")
    return text.upper(), f"길이 {len(text)}"


def build() -> gr.Blocks:
    with gr.Blocks(title="Blocks 레이아웃", analytics_enabled=False) as demo:
        gr.Markdown("# 입력 열과 출력 열")
        with gr.Tab("변환"):
            with gr.Row():
                with gr.Column():
                    message = gr.Textbox(label="문구")
                    button = gr.Button("변환", variant="primary")
                with gr.Column():
                    upper = gr.Textbox(label="결과")
                    meta = gr.Textbox(label="부가")
            button.click(shout, inputs=message, outputs=[upper, meta], api_name="shout")
        with gr.Tab("설명"):
            gr.Markdown("탭은 이 화면 안의 구역이다. 주소 경로로 나누는 법은 study4에서 다룬다.")
    return demo
