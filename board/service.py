"""게시판 공통 API 스펙 v1과 같은 상태 코드와 JSON을 만든다."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from board.errors import error_body
from board.security import hash_password, new_token, token_hash, verify_password
from board.store import Store
from board.validate import validate_post, validate_signup

_SEED_EMAIL = "mina@example.com"
_SEED_PASSWORD = "password123"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def public_user(user: dict) -> dict:
    return {"id": user["id"], "email": user["email"], "nickname": user["nickname"]}


def public_post(post: dict, *, detail: bool) -> dict:
    data = {
        "id": post["id"],
        "title": post["title"],
        "author": {"id": post["authorId"], "nickname": post["authorNickname"]},
        "commentCount": post["commentCount"],
        "createdAt": post["createdAt"],
    }
    if detail:
        data["body"] = post["body"]
        data["tags"] = post["tags"]
        data["updatedAt"] = post["updatedAt"]
    return data


class BoardService:
    def __init__(self, store: Store, token_ttl_seconds: int = 7 * 24 * 3600):
        self.store = store
        self.token_ttl_seconds = token_ttl_seconds
        self._seed()

    def _seed(self) -> None:
        if self.store.get_user_by_email(_SEED_EMAIL):
            return
        now = iso(utc_now())
        user = self.store.create_user(_SEED_EMAIL, hash_password(_SEED_PASSWORD), "mina", now)
        self.store.insert_post("첫 글", "안녕하세요", ["intro"], user["id"], now)
        self.store.insert_post("검색 연습", "Gradio 표에 올릴 두 번째 글", ["note"], user["id"], now)

    def health(self) -> tuple[int, dict]:
        return 200, {"status": "ok"}

    def signup(self, email: str, password: str, nickname: str) -> tuple[int, dict]:
        fields = validate_signup(email, password, nickname)
        if fields:
            return 400, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", fields)
        normalized = email.strip().lower()
        if self.store.get_user_by_email(normalized):
            return 409, error_body("EMAIL_TAKEN", "이미 가입한 이메일입니다.")
        user = self.store.create_user(normalized, hash_password(password), nickname.strip(), iso(utc_now()))
        return 201, {"data": public_user(user)}

    def login(self, email: str, password: str) -> tuple[int, dict]:
        user = self.store.get_user_by_email((email or "").strip().lower())
        if user is None or not verify_password(password or "", user["passwordHash"]):
            return 401, error_body("INVALID_CREDENTIALS", "이메일 또는 비밀번호가 올바르지 않습니다.")
        raw = new_token()
        expires = iso(utc_now() + timedelta(seconds=self.token_ttl_seconds))
        self.store.insert_token(token_hash(raw), user["id"], expires)
        return 200, {"data": {"user": public_user(user), "accessToken": raw}}

    def logout(self, token: str) -> tuple[int, dict | None]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        self.store.delete_token_hash(token_hash(token))
        return 204, None

    def me(self, token: str) -> tuple[int, dict]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        return 200, {"data": public_user(user)}

    def list_posts(self, q: str = "", page: int = 1, limit: int = 10, sort: str = "-createdAt") -> tuple[int, dict]:
        if page < 1:
            return 400, error_body("BAD_REQUEST", "page는 1 이상이어야 합니다.")
        safe_limit = 10 if limit is None else max(1, min(int(limit), 50))
        query = (q or "").strip()
        total = self.store.count_posts(query)
        rows = self.store.list_posts(query, safe_limit, (page - 1) * safe_limit, sort)
        total_pages = max(1, (total + safe_limit - 1) // safe_limit) if total else 1
        return 200, {
            "data": [public_post(row, detail=False) for row in rows],
            "meta": {"page": page, "limit": safe_limit, "total": total, "totalPages": total_pages, "q": query},
        }

    def get_post(self, post_id: int) -> tuple[int, dict]:
        post = self.store.get_post(post_id)
        if post is None:
            return 404, error_body("NOT_FOUND", "글을 찾지 못했습니다.")
        return 200, {"data": public_post(post, detail=True)}

    def create_post(self, token: str, title: str, body: str, tags: list[str]) -> tuple[int, dict]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        fields = validate_post(title, body, tags)
        if fields:
            return 400, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", fields)
        post_id = self.store.insert_post(title.strip(), body.strip(), _clean_tags(tags), user["id"], iso(utc_now()))
        return self._created(post_id)

    def update_post(self, token: str, post_id: int, title: str | None, body: str | None, tags: list[str] | None) -> tuple[int, dict]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        current = self.store.get_post(post_id)
        if current is None:
            return 404, error_body("NOT_FOUND", "글을 찾지 못했습니다.")
        if current["authorId"] != user["id"]:
            return 403, error_body("FORBIDDEN", "작성자만 수정할 수 있습니다.")
        next_title = current["title"] if title is None else title
        next_body = current["body"] if body is None else body
        next_tags = current["tags"] if tags is None else tags
        fields = validate_post(next_title, next_body, next_tags)
        if fields:
            return 400, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", fields)
        self.store.update_post(post_id, next_title.strip(), next_body.strip(), _clean_tags(next_tags), iso(utc_now()))
        updated = self.store.get_post(post_id)
        return 200, {"data": public_post(updated, detail=True)}

    def delete_post(self, token: str, post_id: int) -> tuple[int, dict | None]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        current = self.store.get_post(post_id)
        if current is None:
            return 404, error_body("NOT_FOUND", "글을 찾지 못했습니다.")
        if current["authorId"] != user["id"]:
            return 403, error_body("FORBIDDEN", "작성자만 삭제할 수 있습니다.")
        self.store.delete_post(post_id)
        return 204, None

    def list_comments(self, post_id: int) -> tuple[int, dict]:
        if self.store.get_post(post_id) is None:
            return 404, error_body("NOT_FOUND", "글을 찾지 못했습니다.")
        return 200, {"data": self.store.list_comments(post_id)}

    def create_comment(self, token: str, post_id: int, body: str) -> tuple[int, dict]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        if self.store.get_post(post_id) is None:
            return 404, error_body("NOT_FOUND", "글을 찾지 못했습니다.")
        text = (body or "").strip()
        if not text or len(text) > 1000:
            return 400, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", {"body": ["1~1000자로 입력하세요."]})
        comment_id = self.store.insert_comment(post_id, text, user["id"], iso(utc_now()))
        created = next(item for item in self.store.list_comments(post_id) if item["id"] == comment_id)
        return 201, {"data": created}

    def delete_comment(self, token: str, comment_id: int) -> tuple[int, dict | None]:
        user = self._user_from_token(token)
        if isinstance(user, tuple):
            return user
        current = self.store.get_comment(comment_id)
        if current is None:
            return 404, error_body("NOT_FOUND", "댓글을 찾지 못했습니다.")
        if current["authorId"] != user["id"]:
            return 403, error_body("FORBIDDEN", "작성자만 삭제할 수 있습니다.")
        self.store.delete_comment(comment_id)
        return 204, None

    def _created(self, post_id: int) -> tuple[int, dict]:
        status, payload = self.get_post(post_id)
        if status != 200:
            return status, payload
        return 201, payload

    def _user_from_token(self, token: str):
        if not token:
            return 401, error_body("UNAUTHORIZED", "로그인이 필요합니다.")
        user = self.store.get_user_by_token_hash(token_hash(token), iso(utc_now()))
        if user is None:
            return 401, error_body("UNAUTHORIZED", "로그인이 필요합니다.")
        return user


def _clean_tags(tags: list[str]) -> list[str]:
    return [str(tag).strip() for tag in tags if str(tag).strip()]
