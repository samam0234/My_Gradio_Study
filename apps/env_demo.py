"""study0. 설치된 Gradio와 환경변수 유무만 보여 준다."""

from __future__ import annotations

import os
from pathlib import Path

import gradio as gr

from board.config import load_settings


def build() -> gr.Blocks:
    settings = load_settings()
    with gr.Blocks(title="Gradio 환경", analytics_enabled=False) as demo:
        gr.Markdown("# Gradio 첫 화면")
        gr.Markdown("개발 서버가 이 앱을 띄웠습니다. 주소와 폴더를 확인한 뒤 다음 단원으로 갑니다.")
        gr.Textbox(label="Gradio 버전", value=gr.__version__, interactive=False)
        gr.Textbox(label="APP_ENV", value=settings["app_env"], interactive=False)
        gr.Textbox(label="작업 폴더", value=str(Path.cwd()), interactive=False)
        gr.Textbox(label="API_BASE_URL 설정됨", value=str(bool(os.getenv("API_BASE_URL"))), interactive=False)
        gr.Textbox(label="GRADIO_PORT", value=str(settings["port"]), interactive=False)
    return demo
