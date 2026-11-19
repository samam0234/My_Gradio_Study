"""study17. 타이머로 알림 파일을 다시 읽고, 텍스트 파일을 줄 단위로 처리한다."""

from __future__ import annotations

from pathlib import Path

import gradio as gr

from board.config import load_settings
from board.notify import read_notice, write_notice


def summarize_file(source: str | None) -> str:
    if not source:
        raise gr.Error("파일을 선택하세요.")
    path = Path(source)
    if path.suffix.lower() not in {".txt", ".md"}:
        raise gr.Error("txt 또는 md만 줄 수를 셉니다.")
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    return f"{len(lines)}줄, {len(text)}자"


def build() -> gr.Blocks:
    notice = load_settings()["data_dir"] / "notice.txt"
    with gr.Blocks(title="실시간", analytics_enabled=False) as demo:
        gr.Markdown("# 알림 파일과 텍스트 처리")
        message = gr.Textbox(label="알림 내용")
        live = gr.Textbox(label="5초마다 다시 읽은 알림")
        summary = gr.Textbox(label="파일 요약")
        upload = gr.File(label="txt 또는 md", type="filepath", file_types=[".txt", ".md"])
        gr.Button("알림 남기기").click(lambda text: write_notice(notice, text) or "기록했습니다.", inputs=message, outputs=live)
        timer = gr.Timer(5)
        timer.tick(lambda: read_notice(notice), outputs=live)
        gr.Button("줄 수 세기").click(summarize_file, inputs=upload, outputs=summary, api_name="summarize_file")
    return demo
