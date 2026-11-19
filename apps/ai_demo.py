"""study18. 챗, 스트리밍, 리뷰 표시, MCP로 열 도구."""

from __future__ import annotations

import gradio as gr

from board.ai import analyze_review, answer, stream_text
from board.config import load_settings
from board.gateway import open_gateway
from board.mcp_tools import TOOLS, call_tool

EXAMPLES = [
    "배송이 빠르고 포장도 괜찮았습니다.",
    "지금 클릭하면 공짜 상품과 대박 수익이 있습니다. https://example.test",
]


def mount_ai() -> None:
    settings = load_settings()
    gateway = open_gateway()

    def chat(message, history, document):
        del history
        text = answer(document or "", message or "", settings["model_api_url"], settings["model_api_key"])
        yield from stream_text(text)

    def review(text, image_path):
        try:
            result = analyze_review(text, image_path)
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc
        return result["summary"], result["probabilities"], result["highlights"], result["raw"]

    def tool_call(name, q, document, question):
        arguments = {"q": q, "document": document, "question": question}
        try:
            return call_tool(gateway, name, arguments)
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    gr.Markdown("# 문서 질의와 리뷰 표시")
    gr.Markdown("모델 주소가 없으면 문서 발췌만으로 답한다. 리뷰 탭은 규칙 점수이며 사진을 함께 넣을 수 있다.")
    with gr.Tab("문서 질의"):
        document = gr.Textbox(label="문서", lines=8, value="첫 문단입니다.\n\nGradio는 함수를 화면에 연결합니다.")
        gr.ChatInterface(fn=chat, additional_inputs=[document], title="발췌 챗", api_name="ask_document")
    with gr.Tab("리뷰 표시"):
        with gr.Row():
            with gr.Column():
                text_in = gr.Textbox(label="리뷰 텍스트", lines=6)
                image_in = gr.Image(label="리뷰 사진 (선택)", type="filepath", sources=["upload"])
                button = gr.Button("분석", variant="primary")
                gr.Examples(examples=[[item] for item in EXAMPLES], inputs=[text_in])
            with gr.Column():
                summary_out = gr.Markdown()
                prob_out = gr.Label(label="판정 확률")
                highlight_out = gr.HighlightedText(label="근거 하이라이트")
                json_out = gr.JSON(label="원본 응답")
        button.click(
            review,
            inputs=[text_in, image_in],
            outputs=[summary_out, prob_out, highlight_out, json_out],
            api_name="analyze_review",
        )
    with gr.Tab("MCP 도구"):
        gr.Markdown("이벤트의 `api_name`이 `launch(mcp_server=True)`의 도구가 된다. 아래는 같은 함수를 직접 부르는 연습이다.")
        gr.Code("\n".join(f"{item['name']}: {item['description']}" for item in TOOLS), language="markdown")
        name = gr.Dropdown(choices=[item["name"] for item in TOOLS], value="ask_document", label="도구")
        q = gr.Textbox(label="q")
        doc = gr.Textbox(label="document", lines=4)
        question = gr.Textbox(label="question")
        tool_out = gr.JSON(label="도구 결과")
        gr.Button("호출").click(tool_call, inputs=[name, q, doc, question], outputs=tool_out, api_name="call_tool")


def build() -> gr.Blocks:
    with gr.Blocks(title="AI", analytics_enabled=False) as demo:
        mount_ai()
    return demo
