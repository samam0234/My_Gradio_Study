"""Gradio 이벤트와 같은 일을 하는 작은 도구 목록.

launch(mcp_server=True)는 api_name이 있는 이벤트를 MCP 도구로 연다.
이 모듈은 그 도구를 프로세스 안에서 불러 보는 클라이언트 연습이다.
"""

from __future__ import annotations

from board.ai import ask_document
from board.present import search_table

TOOLS = (
    {
        "name": "search_posts",
        "description": "게시글 제목을 검색해 id와 title 표를 돌려준다.",
        "input": {"q": "string"},
    },
    {
        "name": "ask_document",
        "description": "문서 발췌 안에서만 질문에 답한다.",
        "input": {"document": "string", "question": "string"},
    },
)


def call_tool(gateway, name: str, arguments: dict) -> dict:
    if name == "search_posts":
        rows, caption = search_table(gateway, arguments.get("q", ""))
        return {"rows": rows, "caption": caption}
    if name == "ask_document":
        return {"answer": ask_document(arguments.get("document", ""), arguments.get("question", ""))}
    return {"error": f"unknown tool: {name}"}
