"""study12. 테마와 CSS는 Gradio 6에서 launch 인자다. 이 화면은 그 전 구성을 보여 준다."""

from __future__ import annotations

import gradio as gr


def build() -> gr.Blocks:
    with gr.Blocks(title="화면 구성", analytics_enabled=False) as demo:
        gr.Markdown("# 테마와 입력 묶음")
        gr.Markdown("색과 여백은 `launch(theme=..., css=...)`가 정한다. 입력 칸과 버튼 묶음이 이 프레임워크의 폼이다.")
        with gr.Row():
            with gr.Column():
                name = gr.Textbox(label="이름")
                color = gr.Dropdown(choices=["Soft", "Default", "Glass"], label="테마 이름", value="Soft")
            with gr.Column():
                out = gr.Textbox(label="적용 메모")
        gr.Button("메모").click(lambda n, c: f"{(n or '방문자').strip()} 화면은 {c} 테마 설명을 보고 있습니다.", inputs=[name, color], outputs=out)
    return demo
