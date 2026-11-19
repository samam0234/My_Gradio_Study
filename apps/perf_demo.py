"""study15. 목록 캐시와 비동기 함수, 걸린 시간."""

from __future__ import annotations

import asyncio

import gradio as gr

from board.cache import ListCache, cached_list
from board.gateway import open_gateway

_cache = ListCache()


async def slow_echo(text: str) -> str:
    await asyncio.sleep(0)
    return (text or "").strip() or "비어 있음"


def build() -> gr.Blocks:
    gateway = open_gateway()

    def measured(q: str):
        rows, caption, elapsed, hit = cached_list(gateway, _cache, q or "")
        return rows, f"{caption} · {elapsed:.2f}ms · cache={'hit' if hit else 'miss'}"

    def bust():
        _cache.invalidate()
        return "캐시를 비웠습니다. 다음 검색은 miss입니다."

    with gr.Blocks(title="성능", analytics_enabled=False) as demo:
        gr.Markdown("# 같은 검색은 기억하고, 글이 바뀌면 비운다")
        q = gr.Textbox(label="검색어")
        table = gr.Dataframe(headers=["id", "title"], type="array")
        info = gr.Textbox(label="측정")
        echo = gr.Textbox(label="비동기 결과")
        gr.Button("검색").click(measured, inputs=q, outputs=[table, info], api_name="cached_search")
        gr.Button("캐시 비우기").click(bust, outputs=info)
        gr.Button("비동기 따라 하기").click(slow_echo, inputs=q, outputs=echo)
    return demo
