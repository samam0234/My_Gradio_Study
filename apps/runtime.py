"""개발과 운영에서 launch 인자만 다르게 연다."""

from __future__ import annotations

import logging

import gradio as gr

from board.config import load_settings


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def launch(demo: gr.Blocks) -> None:
    configure_logging()
    settings = load_settings()
    production = settings["app_env"] == "production"
    demo.launch(
        server_name=settings["server_name"],
        server_port=settings["port"],
        share=settings["share"],
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 980px !important; margin: auto; }",
        strict_cors=True,
        show_error=not production,
        mcp_server=settings["mcp"],
        inbrowser=False,
    )


def show(exc: ValueError) -> None:
    raise gr.Error(str(exc)) from exc
