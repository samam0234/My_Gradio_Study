"""로그인과 게시판 CRUD. midpoint와 final이 같은 탭을 쓴다."""

from __future__ import annotations

import gradio as gr

from board.gateway import open_gateway
from board.present import (
    comment_message,
    create_message,
    delete_message,
    login_session,
    post_text,
    search_table,
    signup_message,
    update_message,
)


def mount_board():
    gateway = open_gateway()
    token = gr.State("")

    def run(fn, *args):
        try:
            return fn(*args)
        except ValueError as exc:
            raise gr.Error(str(exc)) from exc

    def search(q: str, page: float):
        return run(search_table, gateway, q, int(page or 1))

    def login(email: str, password: str):
        raw, message = run(login_session, gateway, email, password)
        return raw, message

    def signup(email: str, password: str, nickname: str):
        return run(signup_message, gateway, email, password, nickname)

    def who(raw: str):
        status, payload = gateway.me(raw)
        if status != 200:
            return "로그인 전"
        return f"로그인: {payload['data']['nickname']}"

    def write(raw: str, title: str, body: str, tags: str):
        return run(create_message, gateway, raw, title, body, tags)

    def save(raw: str, post_id: float, title: str, body: str, tags: str):
        return run(update_message, gateway, raw, int(post_id), title, body, tags)

    def remove(raw: str, post_id: float):
        return run(delete_message, gateway, raw, int(post_id))

    def open_one(post_id: float):
        return run(post_text, gateway, int(post_id))

    def add_comment(raw: str, post_id: float, body: str):
        return run(comment_message, gateway, raw, int(post_id), body)

    gr.Markdown("# 게시판")
    status = gr.Textbox(label="상태", interactive=False)
    with gr.Tab("검색"):
        query = gr.Textbox(label="검색어")
        page = gr.Number(label="쪽", value=1, precision=0)
        table = gr.Dataframe(headers=["id", "title"], datatype=["number", "str"], type="array", label="결과")
        caption = gr.Textbox(label="목록 정보", interactive=False)
        gr.Button("검색").click(search, inputs=[query, page], outputs=[table, caption], api_name="search_posts")
    with gr.Tab("상세"):
        post_id = gr.Number(label="글 번호", value=1, precision=0)
        detail = gr.Textbox(label="본문과 댓글", lines=10)
        comment = gr.Textbox(label="댓글")
        gr.Button("열기").click(open_one, inputs=post_id, outputs=detail, api_name="read_post")
        gr.Button("댓글 등록").click(add_comment, inputs=[token, post_id, comment], outputs=status).then(
            open_one, inputs=post_id, outputs=detail
        )
    with gr.Tab("작성"):
        title = gr.Textbox(label="제목")
        body = gr.Textbox(label="본문", lines=6)
        tags = gr.Textbox(label="태그", placeholder="쉼표로 구분")
        gr.Button("등록", variant="primary").click(
            write, inputs=[token, title, body, tags], outputs=status, concurrency_limit=1, api_name="create_post"
        )
    with gr.Tab("수정·삭제"):
        edit_id = gr.Number(label="글 번호", precision=0)
        edit_title = gr.Textbox(label="제목")
        edit_body = gr.Textbox(label="본문", lines=6)
        edit_tags = gr.Textbox(label="태그")
        gr.Button("수정").click(save, inputs=[token, edit_id, edit_title, edit_body, edit_tags], outputs=status, api_name="update_post")
        gr.Button("삭제").click(remove, inputs=[token, edit_id], outputs=status, api_name="delete_post")
    with gr.Tab("계정"):
        email = gr.Textbox(label="이메일")
        password = gr.Textbox(label="비밀번호", type="password")
        nickname = gr.Textbox(label="닉네임")
        gr.Button("가입").click(signup, inputs=[email, password, nickname], outputs=status)
        gr.Button("로그인").click(login, inputs=[email, password], outputs=[token, status]).then(who, inputs=token, outputs=status)
        gr.Button("내 정보").click(who, inputs=token, outputs=status)
        gr.Button("로그아웃").click(lambda: ("", "로그아웃했습니다."), outputs=[token, status])
    return token
