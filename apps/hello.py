"""study1. Interface 한 함수로 첫 응답을 만든다."""

from __future__ import annotations

import gradio as gr


def greet(name: str, topic: str) -> str:
    who = (name or "").strip() or "방문자"
    picked = topic or "출력"
    return f"{who}님, 오늘은 {picked}을 봅니다."


def build() -> gr.Interface:
    return gr.Interface(
        fn=greet,
        inputs=[
            gr.Textbox(label="이름", value="방문자"),
            gr.Dropdown(choices=["출력", "입력", "이벤트"], label="오늘 볼 것", value="출력"),
        ],
        outputs=gr.Textbox(label="응답"),
        title="안녕하세요, Gradio",
        description="함수 반환값이 화면의 응답입니다.",
        examples=[["민아", "출력"]],
        api_name="greet",
        analytics_enabled=False,
    )
