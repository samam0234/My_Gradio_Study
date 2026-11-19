"""study11~18과 midpoint를 한 앱에 모은 최종 화면."""

from __future__ import annotations

import json

import gradio as gr

from apps.ai_demo import mount_ai
from apps.board_ui import mount_board
from apps.ops_demo import mount_ops
from board.config import load_settings
from board.dburl import describe_database


def build() -> gr.Blocks:
    settings = load_settings()
    with gr.Blocks(title="Gradio 서비스", analytics_enabled=False) as demo:
        gr.Markdown("# Gradio 하나로 만든 게시판")
        gr.Markdown(
            "계정과 글, 파일, 문서 질의, 운영 점검을 이 화면에서 이어서 확인한다. "
            f"저장 종류: {json.dumps(describe_database(settings['database_url']), ensure_ascii=False)}"
        )
        with gr.Tab("게시판"):
            mount_board()
        with gr.Tab("AI"):
            mount_ai()
        with gr.Tab("운영"):
            mount_ops()
    return demo
