"""study3. State, 브라우저 저장, JSON 파일을 나눈다."""

from __future__ import annotations

import gradio as gr

from board.config import load_settings
from board.notes import load_notes, save_note
from board.service import iso, utc_now


def build() -> gr.Blocks:
    path = load_settings()["data_dir"] / "notes.json"

    def remember(text: str, nickname: str, count: int):
        if not (text or "").strip():
            raise gr.Error("메모를 입력하세요.")
        notes = save_note(path, nickname, text, iso(utc_now()))
        lines = [f"{item['at']} {item['nickname']}: {item['text']}" for item in notes]
        return count + 1, "\n".join(lines), nickname, ""

    with gr.Blocks(title="데이터", analytics_enabled=False) as demo:
        gr.Markdown("# 세션, 브라우저, 파일")
        count = gr.State(0)
        nickname = gr.BrowserState("방문자", storage_key="gradio-study-nickname")
        with gr.Row():
            name = gr.Textbox(label="표시 이름")
            text = gr.Textbox(label="메모")
        button = gr.Button("파일에 저장")
        seen = gr.Number(label="이번 세션에서 저장한 횟수", interactive=False)
        board = gr.Textbox(label="JSON 파일에 있는 메모", lines=8, interactive=False)
        button.click(remember, inputs=[text, name, count], outputs=[count, board, nickname, text])
        demo.load(lambda stored: (stored, "\n".join(f"{item['at']} {item['nickname']}: {item['text']}" for item in load_notes(path))), inputs=nickname, outputs=[name, board])
    return demo
