"""study13. 파일, 사진, 메일 기록, 결제 링크, 모의 OAuth."""

from __future__ import annotations

import gradio as gr

from board.config import load_settings
from board.files import save_upload
from board.mail import send_or_store


def build() -> gr.Blocks:
    settings = load_settings()
    upload_dir = settings["data_dir"] / "uploads"
    outbox = settings["data_dir"] / "outbox" / "last.json"

    def store_files(file_path, image_path):
        try:
            saved = save_upload(file_path, upload_dir)
            image = save_upload(image_path, upload_dir, image_only=True)
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc
        return f"파일 {saved['name'] or '없음'} / 사진 {image['name'] or '없음'}"

    def mail(recipient, subject, body):
        try:
            return send_or_store(outbox, recipient, subject, body, settings)
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    def pay(order_name, amount):
        if not (order_name or "").strip() or amount is None or float(amount) <= 0:
            raise gr.Error("주문명과 0보다 큰 금액이 필요합니다.")
        return f"{settings['payment_base']}?order={order_name.strip()}&amount={int(amount)}"

    def oauth_link():
        client_id = settings["oauth_client_id"]
        if not client_id:
            return "OAUTH_CLIENT_ID가 없습니다. 아래 모의 콜백으로 로그인 표시만 연습합니다."
        return f"https://github.com/login/oauth/authorize?client_id={client_id}&scope=read:user"

    def mock_callback(code: str):
        if settings["oauth_mode"] != "mock":
            raise gr.Error("OAUTH_MODE=mock 일 때만 모의 콜백을 사용합니다.")
        if (code or "").strip() != "demo-code":
            raise gr.Error("모의 코드는 demo-code 입니다.")
        return "모의 소셜 로그인: demo-user"

    with gr.Blocks(title="외부 연동", analytics_enabled=False) as demo:
        gr.Markdown("# 파일과 외부 서비스")
        with gr.Tab("업로드"):
            file_in = gr.File(label="파일", type="filepath")
            image_in = gr.Image(label="사진", type="filepath", sources=["upload"])
            file_out = gr.Textbox(label="저장된 이름")
            gr.Button("저장").click(store_files, inputs=[file_in, image_in], outputs=file_out, api_name="save_upload")
        with gr.Tab("메일"):
            recipient = gr.Textbox(label="받는 사람")
            subject = gr.Textbox(label="제목")
            body = gr.Textbox(label="본문", lines=4)
            mail_out = gr.Textbox(label="결과")
            gr.Button("보내기").click(mail, inputs=[recipient, subject, body], outputs=mail_out)
        with gr.Tab("결제 링크"):
            order_name = gr.Textbox(label="주문명")
            amount = gr.Number(label="금액", precision=0)
            pay_out = gr.Textbox(label="이동할 주소")
            gr.Button("링크 만들기").click(pay, inputs=[order_name, amount], outputs=pay_out)
        with gr.Tab("소셜 로그인"):
            link = gr.Textbox(label="인가 주소")
            code = gr.Textbox(label="모의 code", value="demo-code")
            who = gr.Textbox(label="결과")
            gr.Button("인가 주소 보기").click(oauth_link, outputs=link)
            gr.Button("모의 콜백").click(mock_callback, inputs=code, outputs=who)
    return demo
