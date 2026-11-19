"""study0~10만으로 구성하는 작은 게시판."""

from __future__ import annotations

import gradio as gr

from apps.board_ui import mount_board


def build() -> gr.Blocks:
    with gr.Blocks(title="Gradio 게시판", analytics_enabled=False) as demo:
        mount_board()
    return demo
