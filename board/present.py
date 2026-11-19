"""화면이 표와 문장으로 바꾸기 직전에 쓰는 변환."""

from __future__ import annotations

from board.errors import format_error
from board.locks import try_lock
from board.validate import parse_tags


def search_table(gateway, q: str, page: int = 1) -> tuple[list[list], str]:
    status, payload = gateway.list_posts(q=q or "", page=page, limit=10)
    if status != 200:
        raise ValueError(format_error(status, payload))
    rows = [[item["id"], item["title"]] for item in payload["data"]]
    meta = payload["meta"]
    caption = f"{meta['total']}건 · {meta['page']}/{meta['totalPages']}쪽"
    if meta["q"]:
        caption = f"검색어 {meta['q']} · " + caption
    return rows, caption


def post_text(gateway, post_id: int) -> str:
    status, payload = gateway.get_post(int(post_id))
    if status != 200:
        raise ValueError(format_error(status, payload))
    data = payload["data"]
    comments = gateway.list_comments(int(post_id))
    comment_lines = []
    if comments[0] == 200:
        for item in comments[1]["data"]:
            comment_lines.append(f"- {item['author']['nickname']}: {item['body']}")
    extra = "\n".join(comment_lines) if comment_lines else "댓글 없음"
    tags = ", ".join(data.get("tags") or [])
    return (
        f"{data['title']}\n{data['body']}\n작성자 {data['author']['nickname']}\n"
        f"태그 {tags}\n\n{extra}"
    )


def login_session(gateway, email: str, password: str) -> tuple[str, str]:
    status, payload = gateway.login(email, password)
    if status != 200:
        raise ValueError(format_error(status, payload))
    user = payload["data"]["user"]
    return payload["data"]["accessToken"], f"{user['nickname']} 님으로 로그인했습니다."


def signup_message(gateway, email: str, password: str, nickname: str) -> str:
    status, payload = gateway.signup(email, password, nickname)
    if status not in {200, 201}:
        raise ValueError(format_error(status, payload))
    return f"{payload['data']['nickname']} 님, 가입되었습니다. 이어서 로그인하세요."


def create_message(gateway, token: str, title: str, body: str, tags_raw: str) -> str:
    guard = try_lock(token or "anonymous")
    if guard is None:
        raise ValueError("429 RATE_LIMITED: 이전 제출이 끝나기 전에 다시 눌렸습니다.")
    try:
        status, payload = gateway.create_post(token, title, body, parse_tags(tags_raw))
    finally:
        guard.release()
    if status != 201:
        raise ValueError(format_error(status, payload))
    return f"201 작성 완료. 글 번호 {payload['data']['id']}"


def update_message(gateway, token: str, post_id: int, title: str, body: str, tags_raw: str) -> str:
    status, payload = gateway.update_post(token, int(post_id), title, body, parse_tags(tags_raw))
    if status != 200:
        raise ValueError(format_error(status, payload))
    return f"200 수정 완료. 글 번호 {payload['data']['id']}"


def delete_message(gateway, token: str, post_id: int) -> str:
    status, payload = gateway.delete_post(token, int(post_id))
    if status != 204:
        raise ValueError(format_error(status, payload))
    return "204 삭제했습니다."


def comment_message(gateway, token: str, post_id: int, body: str) -> str:
    status, payload = gateway.create_comment(token, int(post_id), body)
    if status != 201:
        raise ValueError(format_error(status, payload))
    return "201 댓글을 남겼습니다."
