import threading
from pathlib import Path

import pytest
import requests
from fastapi.testclient import TestClient

from board.ai import analyze_review, answer, ask_document, highlight, stream_text
from board.cache import ListCache, cached_list
from board.dburl import describe_database, sqlite_path
from board.errors import format_error
from board.files import save_upload
from board.mail import send_or_store
from board.mcp_tools import call_tool
from board.notes import save_note
from board.present import create_message, login_session, search_table
from board.remote import RemoteBoard
from board.security import hash_password, verify_password
from board.service import BoardService
from board.store import Store
from tools.mock_api import create_app


def service(tmp_path: Path) -> BoardService:
    return BoardService(Store(tmp_path / "board.db"))


def test_seed_login_and_search(tmp_path: Path):
    board = service(tmp_path)
    status, payload = board.login("mina@example.com", "password123")
    assert status == 200
    assert "password" not in payload["data"]["user"]
    rows, caption = search_table(board, "첫")
    assert rows[0][1] == "첫 글"
    assert "1건" in caption


def test_signup_validation_and_duplicate(tmp_path: Path):
    board = service(tmp_path)
    status, payload = board.signup("bad", "short", "")
    assert status == 400
    assert "email" in payload["error"]["fields"]
    assert "1~30자" in format_error(status, payload)
    created, _ = board.signup("new@example.com", "password123", "nuri")
    assert created == 201
    again, payload = board.signup("new@example.com", "password123", "nuri")
    assert again == 409
    assert payload["error"]["code"] == "EMAIL_TAKEN"


def test_crud_permissions(tmp_path: Path):
    board = service(tmp_path)
    _, mina = board.login("mina@example.com", "password123")
    token = mina["data"]["accessToken"]
    missing, _ = board.create_post("", "제목", "본문", [])
    assert missing == 401
    status, created = board.create_post(token, "새 글", "본문입니다", ["a"])
    assert status == 201
    post_id = created["data"]["id"]
    assert "passwordHash" not in created["data"]
    other, _ = board.signup("other@example.com", "password123", "other")
    assert other == 201
    _, other_login = board.login("other@example.com", "password123")
    forbidden, payload = board.delete_post(other_login["data"]["accessToken"], post_id)
    assert forbidden == 403
    assert payload["error"]["code"] == "FORBIDDEN"
    gone, empty = board.delete_post(token, post_id)
    assert gone == 204
    assert empty is None
    not_found, _ = board.get_post(post_id)
    assert not_found == 404


def test_bad_login_hides_which_field(tmp_path: Path):
    board = service(tmp_path)
    status, payload = board.login("mina@example.com", "wrong-password")
    assert status == 401
    assert payload["error"]["code"] == "INVALID_CREDENTIALS"
    assert "이메일" in payload["error"]["message"] and "비밀번호" in payload["error"]["message"]


def test_page_and_limit(tmp_path: Path):
    board = service(tmp_path)
    status, payload = board.list_posts(page=0)
    assert status == 400
    status, payload = board.list_posts(limit=99)
    assert payload["meta"]["limit"] == 50


def test_comment_and_logout(tmp_path: Path):
    board = service(tmp_path)
    _, session = board.login("mina@example.com", "password123")
    token = session["data"]["accessToken"]
    _, posts = board.list_posts()
    post_id = posts["data"][0]["id"]
    status, _ = board.create_comment(token, post_id, "좋아요")
    assert status == 201
    listed, payload = board.list_comments(post_id)
    assert listed == 200
    assert payload["data"][0]["body"] == "좋아요"
    logged_out, _ = board.logout(token)
    assert logged_out == 204
    me, _ = board.me(token)
    assert me == 401


def test_password_hash_roundtrip():
    stored = hash_password("password123")
    assert verify_password("password123", stored)
    assert not verify_password("password124", stored)


def test_duplicate_submit_is_rejected(tmp_path: Path):
    board = service(tmp_path)
    token, _ = login_session(board, "mina@example.com", "password123")
    started = threading.Event()
    release = threading.Event()
    original = board.create_post

    def slow(*args, **kwargs):
        started.set()
        release.wait(1)
        return original(*args, **kwargs)

    board.create_post = slow
    errors = []

    def worker():
        try:
            create_message(board, token, "겹침", "본문입니다", "")
        except ValueError as exc:
            errors.append(str(exc))

    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker)
    first.start()
    assert started.wait(1)
    second.start()
    second.join(1)
    release.set()
    first.join(1)
    assert any("429" in item for item in errors)


def test_remote_maps_422(monkeypatch):
    class Response:
        status_code = 422
        content = b"{}"

        def json(self):
            return {"detail": [{"loc": ["body", "title"], "msg": "field required"}]}

    monkeypatch.setattr("board.remote.requests.request", lambda *args, **kwargs: Response())
    status, payload = RemoteBoard("http://127.0.0.1:8000").create_post("token", "", "", [])
    assert status == 422
    assert "title" in payload["error"]["fields"]


def test_remote_connection_error(monkeypatch):
    def boom(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr("board.remote.requests.request", boom)
    status, payload = RemoteBoard("http://127.0.0.1:9").health()
    assert status == 503
    assert payload["error"]["code"] == "UPSTREAM"


def test_mock_api_login_and_location(tmp_path: Path):
    client = TestClient(create_app(tmp_path / "mock.db"))
    health = client.get("/health")
    assert health.status_code == 200
    assert health.headers["x-request-id"]
    login = client.post("/api/auth/login", json={"email": "mina@example.com", "password": "password123"})
    token = login.json()["data"]["accessToken"]
    created = client.post(
        "/api/posts",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "API 글", "body": "본문", "tags": ["api"]},
    )
    assert created.status_code == 201
    assert created.headers["location"].startswith("/api/posts/")
    listed = client.get("/api/posts", params={"q": "API"})
    assert listed.json()["data"][0]["title"] == "API 글"


def test_database_url_descriptions():
    assert describe_database("sqlite:///data/board.db")["dialect"] == "sqlite"
    assert describe_database("postgresql://localhost/board")["server"] is True
    assert describe_database("mariadb://localhost/board")["dialect"] == "mariadb"
    assert describe_database("mongodb://localhost/board")["dialect"] == "mongodb"
    path = sqlite_path("sqlite:///data/board.db")
    assert path.name == "board.db"


def test_notes_files_and_mail(tmp_path: Path):
    notes = save_note(tmp_path / "notes.json", "민아", "메모", "2026-11-19T00:00:00Z")
    assert notes[0]["text"] == "메모"
    source = tmp_path / "note.txt"
    source.write_text("hello", encoding="utf-8")
    saved = save_upload(str(source), tmp_path / "uploads")
    assert saved["saved"] is True
    big = tmp_path / "big.txt"
    big.write_bytes(b"a" * (2 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="413"):
        save_upload(str(big), tmp_path / "uploads")
    message = send_or_store(tmp_path / "outbox.json", "mina@example.com", "제목", "본문", {"smtp_host": ""})
    assert "보낸편지" in message


def test_ai_excerpt_review_and_stream():
    assert ask_document("", "질문") == "문서에서 찾을 수 없습니다."
    answer_text = ask_document("첫 문단입니다.\n\nGradio는 함수를 화면에 연결합니다.", "Gradio 함수")
    assert "(발췌 2)" in answer_text
    assert "찾을 수 없습니다" in ask_document("다른 이야기", "Gradio")
    result = analyze_review("지금 클릭하면 공짜 상품 대박", None)
    assert result["raw"]["label"] == "Fake"
    assert any(label == "suspicious" for _text, label in result["highlights"])
    with pytest.raises(ValueError):
        analyze_review("  ", None)
    streamed = list(stream_text("ab"))
    assert streamed[-1] == "ab"
    plain = highlight("안녕")
    assert plain == [("안녕", None)]
    fallback = answer("Gradio 문장", "Gradio", model_url="", model_key="")
    assert "발췌" in fallback


def test_cache_and_mcp(tmp_path: Path):
    board = service(tmp_path)
    cache = ListCache()
    first = cached_list(board, cache, "첫")
    second = cached_list(board, cache, "첫")
    assert first[3] is False
    assert second[3] is True
    cache.invalidate()
    third = cached_list(board, cache, "첫")
    assert third[3] is False
    tool = call_tool(board, "ask_document", {"document": "Gradio 함수", "question": "Gradio"})
    assert "발췌" in tool["answer"]
    rows = call_tool(board, "search_posts", {"q": "첫"})
    assert rows["rows"][0][1] == "첫 글"
    assert "error" in call_tool(board, "missing", {})
