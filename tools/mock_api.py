"""공통 스펙 v1을 HTTP로 여는 연습 서버. Gradio와 포트를 나누기 위해 8000을 쓴다."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from board.config import ROOT, load_settings
from board.service import BoardService
from board.store import Store
from board.validate import validate_post

app = FastAPI(title="Board mock", docs_url="/api-docs", openapi_url="/openapi.json")


def _service() -> BoardService:
    path = Path(getattr(app.state, "db_path", ROOT / "data" / "mock.db"))
    if not hasattr(app.state, "service"):
        app.state.service = BoardService(Store(path))
    return app.state.service


@app.middleware("http")
async def request_id(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.headers.get("x-request-id") or str(uuid.uuid4())
    return response


def _json(status: int, payload):
    if status == 204:
        return Response(status_code=204)
    response = JSONResponse(payload, status_code=status)
    return response


def _token(request: Request) -> str:
    header = request.headers.get("authorization", "")
    if header.lower().startswith("bearer "):
        return header.split(" ", 1)[1].strip()
    return ""


@app.get("/health")
def health():
    status, payload = _service().health()
    return _json(status, payload)


@app.post("/api/auth/signup")
async def signup(request: Request):
    body = await request.json()
    status, payload = _service().signup(body.get("email", ""), body.get("password", ""), body.get("nickname", ""))
    return _json(status, payload)


@app.post("/api/auth/login")
async def login(request: Request):
    body = await request.json()
    status, payload = _service().login(body.get("email", ""), body.get("password", ""))
    return _json(status, payload)


@app.post("/api/auth/logout")
def logout(request: Request):
    status, payload = _service().logout(_token(request))
    return _json(status, payload)


@app.get("/api/auth/me")
def me(request: Request):
    status, payload = _service().me(_token(request))
    return _json(status, payload)


@app.get("/api/posts")
def list_posts(q: str = "", page: int = 1, limit: int = 10, sort: str = "-createdAt"):
    status, payload = _service().list_posts(q, page, limit, sort)
    return _json(status, payload)


@app.get("/api/posts/{post_id}")
def get_post(post_id: int):
    status, payload = _service().get_post(post_id)
    return _json(status, payload)


@app.post("/api/posts")
async def create_post(request: Request):
    body = await request.json()
    title = body.get("title", "")
    text = body.get("body", "")
    tags = body.get("tags") or []
    fields = validate_post(title, text, tags)
    status, payload = _service().create_post(_token(request), title, text, tags)
    response = _json(status, payload)
    if status == 201 and isinstance(payload, dict):
        response.headers["Location"] = f"/api/posts/{payload['data']['id']}"
    if fields and status == 400:
        return response
    return response


@app.patch("/api/posts/{post_id}")
async def update_post(post_id: int, request: Request):
    body = await request.json()
    status, payload = _service().update_post(
        _token(request),
        post_id,
        body["title"] if "title" in body else None,
        body["body"] if "body" in body else None,
        body["tags"] if "tags" in body else None,
    )
    return _json(status, payload)


@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, request: Request):
    status, payload = _service().delete_post(_token(request), post_id)
    return _json(status, payload)


@app.get("/api/posts/{post_id}/comments")
def list_comments(post_id: int):
    status, payload = _service().list_comments(post_id)
    return _json(status, payload)


@app.post("/api/posts/{post_id}/comments")
async def create_comment(post_id: int, request: Request):
    body = await request.json()
    status, payload = _service().create_comment(_token(request), post_id, body.get("body", ""))
    return _json(status, payload)


@app.delete("/api/comments/{comment_id}")
def delete_comment(comment_id: int, request: Request):
    status, payload = _service().delete_comment(_token(request), comment_id)
    return _json(status, payload)


def create_app(db_path: Path, origin: str = "http://127.0.0.1:7860") -> FastAPI:
    local = FastAPI(title="Board mock", docs_url="/api-docs")
    local.add_middleware(
        CORSMiddleware,
        allow_origins=[origin],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    local.state.service = BoardService(Store(db_path))

    @local.middleware("http")
    async def request_id(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.headers.get("x-request-id") or str(uuid.uuid4())
        return response

    def service() -> BoardService:
        return local.state.service

    @local.get("/health")
    def health_route():
        status, payload = service().health()
        return _json(status, payload)

    @local.post("/api/auth/login")
    async def login_route(request: Request):
        body = await request.json()
        status, payload = service().login(body.get("email", ""), body.get("password", ""))
        return _json(status, payload)

    @local.get("/api/posts")
    def posts_route(q: str = "", page: int = 1, limit: int = 10, sort: str = "-createdAt"):
        status, payload = service().list_posts(q, page, limit, sort)
        return _json(status, payload)

    @local.post("/api/posts")
    async def create_route(request: Request):
        body = await request.json()
        status, payload = service().create_post(_token(request), body.get("title", ""), body.get("body", ""), body.get("tags") or [])
        response = _json(status, payload)
        if status == 201:
            response.headers["Location"] = f"/api/posts/{payload['data']['id']}"
        return response

    return local


if __name__ == "__main__":
    import uvicorn

    settings = load_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings["cors_origin"]],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    uvicorn.run(app, host="127.0.0.1", port=8000)
