"""POST_SOURCE=api 일 때 공통 스펙 서버를 requests로 호출한다."""

from __future__ import annotations

import requests

from board.errors import error_body


class RemoteBoard:
    def __init__(self, base_url: str, timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> tuple[int, dict]:
        return self._request("GET", "/health")

    def signup(self, email: str, password: str, nickname: str) -> tuple[int, dict]:
        return self._request("POST", "/api/auth/signup", json={"email": email, "password": password, "nickname": nickname})

    def login(self, email: str, password: str) -> tuple[int, dict]:
        return self._request("POST", "/api/auth/login", json={"email": email, "password": password})

    def logout(self, token: str) -> tuple[int, dict | None]:
        return self._request("POST", "/api/auth/logout", token=token)

    def me(self, token: str) -> tuple[int, dict]:
        return self._request("GET", "/api/auth/me", token=token)

    def list_posts(self, q: str = "", page: int = 1, limit: int = 10, sort: str = "-createdAt") -> tuple[int, dict]:
        return self._request("GET", "/api/posts", params={"q": q, "page": page, "limit": limit, "sort": sort})

    def get_post(self, post_id: int) -> tuple[int, dict]:
        return self._request("GET", f"/api/posts/{post_id}")

    def create_post(self, token: str, title: str, body: str, tags: list[str]) -> tuple[int, dict]:
        return self._request("POST", "/api/posts", token=token, json={"title": title, "body": body, "tags": tags})

    def update_post(self, token: str, post_id: int, title: str | None, body: str | None, tags: list[str] | None) -> tuple[int, dict]:
        payload = {}
        if title is not None:
            payload["title"] = title
        if body is not None:
            payload["body"] = body
        if tags is not None:
            payload["tags"] = tags
        return self._request("PATCH", f"/api/posts/{post_id}", token=token, json=payload)

    def delete_post(self, token: str, post_id: int) -> tuple[int, dict | None]:
        return self._request("DELETE", f"/api/posts/{post_id}", token=token)

    def list_comments(self, post_id: int) -> tuple[int, dict]:
        return self._request("GET", f"/api/posts/{post_id}/comments")

    def create_comment(self, token: str, post_id: int, body: str) -> tuple[int, dict]:
        return self._request("POST", f"/api/posts/{post_id}/comments", token=token, json={"body": body})

    def delete_comment(self, token: str, comment_id: int) -> tuple[int, dict | None]:
        return self._request("DELETE", f"/api/comments/{comment_id}", token=token)

    def _request(self, method: str, path: str, token: str = "", **kwargs):
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        if "json" in kwargs:
            headers["Content-Type"] = "application/json; charset=utf-8"
        try:
            response = requests.request(
                method,
                f"{self.base_url}{path}",
                headers=headers,
                timeout=self.timeout,
                **kwargs,
            )
        except requests.RequestException:
            return 503, error_body("UPSTREAM", "API 서버에 연결하지 못했습니다.")
        if response.status_code == 204 or not response.content:
            return response.status_code, None
        try:
            payload = response.json()
        except ValueError:
            return response.status_code, error_body("UPSTREAM", "API 응답이 JSON이 아닙니다.")
        if response.status_code == 422 and "error" not in payload:
            return 422, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", _fields_from_detail(payload))
        return response.status_code, payload


def _fields_from_detail(payload: dict) -> dict | None:
    detail = payload.get("detail")
    if isinstance(detail, list):
        fields: dict = {}
        for item in detail:
            loc = item.get("loc") or ["body"]
            key = str(loc[-1])
            fields.setdefault(key, []).append(str(item.get("msg") or "형식을 확인하세요."))
        return fields
    return None
