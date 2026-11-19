# study9. 테스트·디버깅

## ① 목표

게시판 규칙과 화면이 만들어지는지를 pytest로 고정하고, 원격 API는 가짜 응답으로 바꾸며, 로그와 자주 나는 오류를 보고 고치는 순서를 익힌다.

## ② 📖 이론

### 왜 쓰는지

화면을 손으로만 누르면 해시가 응답에 섞여 들어와도 놓친다. 테스트는 상태 코드와 필드 문장을 문장으로 고정한다. Gradio 이벤트는 결국 Python 함수이므로, 브라우저 없이 그 함수를 부를 수 있다. 네트워크가 필요한 부분은 소켓을 열지 않고 `requests`를 바꿔 치운다.

### 핵심 개념

- **단위 테스트**: `BoardService`를 임시 SQLite에 붙여 가입, 권한, 페이지를 본다.
- **요청 테스트**: FastAPI `TestClient`로 mock 서버의 `/health`, 로그인, `Location`을 본다.
- **mock**: `monkeypatch`로 `board.remote.requests.request`를 가짜 응답 함수로 바꾼다.
- **화면 생성 테스트**: 각 `build()`가 `gr.Blocks`를 돌려주는지만 확인한다. 브라우저 클릭 전체를 CI에 넣지 않는다.
- **로그**: `logging.basicConfig`가 표준 출력에 남긴다. 토큰과 키는 로그 포맷에 넣지 않는다.
- **디버거**: 에디터의 Python 디버거로 `create_post`에 멈추면 `token`이 빈 문자열인지 바로 보인다.

### 비유

테스트는 영업 전에 저울 추를 올리는 일이다. 손님(브라우저)을 부르지 않아도 저울이 200을 가리키는지 알 수 있다. 옆 가게(API)는 간판만 가짜로 세워 둔다.

## ③ 🛠️ 실기

실행:

```powershell
pytest -q
```

`tests/test_board.py`가 서비스, 422 변환, mock 서버, 파일 크기, 발췌 답변, 캐시를 본다. `tests/test_apps.py`는 화면 모듈 16개가 `Blocks`를 만드는지 본다.

422를 가짜로 만드는 테스트:

```python
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
```

연결 실패는 `requests.ConnectionError`를 일으키게 바꿔 503 `UPSTREAM`을 확인한다. 테스트 데이터베이스는 `tmp_path`라 `data/board.db`를 더럽히지 않는다.

디버깅 순서:

1. 터미널의 traceback에서 파일과 줄 번호를 본다.
2. 상태 코드가 401이면 토큰 상태부터 본다.
3. 400이면 `error.fields`를 본다.
4. 503이면 mock 프로세스와 `API_BASE_URL`을 본다.
5. 그래도 화면만 이상하면 브라우저 Network의 `/gradio_api/` 상태 코드를 본다.

### 줄별 설명

- `pytest -q`: 점 하나당 테스트 하나. 실패 시 짧은 traceback을 보여 준다.
- `tmp_path`: pytest가 테스트마다 주는 임시 폴더다.
- `monkeypatch.setattr`: 테스트가 끝나면 원래 `requests.request`로 돌아간다.
- `status_code = 422`: 원격이 검증 실패를 422로 준 척한다.
- `detail`: FastAPI 기본 형식. `RemoteBoard`가 `fields`로 바꾼다.
- `TestClient`: 포트를 열지 않고 ASGI 앱을 호출한다.
- `isinstance(demo, gr.Blocks)`: 컴포넌트 인자가 잘못된 화면은 여기서 바로 실패한다.

### 자주 나는 오류 10가지

| # | 증상 | 원인 | 해결 |
| --- | --- | --- | --- |
| 1 | `gradio`를 찾을 수 없음 | 가상환경이 꺼짐 | `.venv` 활성화 |
| 2 | 포트 사용 중 | 이전 서버 | `Ctrl+C` 또는 `GRADIO_PORT` |
| 3 | `ModuleNotFoundError: apps` | 루트 밖에서 실행 | 저장소 루트에서 실행 |
| 4 | 빈 검색 결과 | 쿼리가 너무 김 | 검색어를 비워 전체 확인 |
| 5 | 작성 401 | `State`에 토큰이 없음 | 로그인 출력 순서 |
| 6 | 400인데 필드가 안 보임 | 422 본문을 안 바꿈 | `RemoteBoard` 분기 |
| 7 | 403 | 남의 글 | 작성자 토큰으로 다시 |
| 8 | 503 UPSTREAM | API 프로세스 중지 | `/health` 확인 |
| 9 | `Language text not supported` | `gr.Code(language="text")` | `markdown` 또는 `json` |
| 10 | 한글이 테스트 출력에서 깨져 보임 | 콘솔 코드 페이지 | 단언은 한글 조각으로 하고 파일은 UTF-8 |

## ④ 🔗 연동 포인트

- DB를 쓰는 테스트는 임시 파일의 `Store`다. 공유 `data/board.db`를 열지 않는다.
- API를 쓰는 테스트는 `requests.request`를 바꾸거나 `TestClient`를 쓴다. 둘 다 바깥 네트워크가 필요 없다.
- CI는 `.github/workflows/ci.yml`이 같은 `pytest -q`를 실행한다. study16이 그 파일을 점검표에 넣는다.

## ⑤ 오류 노트

### 테스트가 서로 글을 봅니다

- 증상: 혼자 돌리면 되고 전체 실행에서 개수가 어긋난다.
- 원인: 같은 SQLite 파일을 테스트가 공유한다.
- 해결: `service(tmp_path)`처럼 테스트마다 파일을 만든다.

### mock이 실제 서버를 침

- 증상: 테스트 중에 `data/mock.db`가 생긴다.
- 원인: `monkeypatch` 경로가 `requests.request`가 아니라 다른 이름이다.
- 해결: `board.remote.requests.request`처럼 그 모듈이 쓰는 이름을 바꾼다.

### 화면 테스트가 서버를 띄움

- 증상: pytest가 끝나지 않는다.
- 원인: `build()` 밖에서 `launch()`를 import 시점에 호출했다.
- 해결: `launch`는 `if __name__ == "__main__"` 안에만 둔다.

## ⑥ 직접 해보기

1. `pytest -q`가 모두 통과하는지 확인한다.
2. 제목 검증 문장을 일부러 한 글자 바꿔 테스트가 실패하는 줄을 보고 되돌린다.
3. 없는 글 번호를 midpoint에서 눌러 터미널 로그와 화면 오류 창이 같이 나는지 본다.

## ⑦ ☐ 체크리스트

- [ ] `pytest -q`가 통과한다.
- [ ] 서비스 테스트는 임시 SQLite를 쓴다.
- [ ] 422와 연결 실패는 `requests`를 바꿔 확인한다.
- [ ] mock 서버는 `TestClient`로 포트 없이 호출한다.
- [ ] `launch()`가 import 시점에 돌지 않는다.
- [ ] 위 10가지 증상 중 401과 503의 첫 확인 위치를 말할 수 있다.

## ⑧ 다음 단계

테스트가 규칙을 고정한 상태에서, study10은 이 앱을 임시 공개 링크, Spaces, Docker 중 어디에 올리는지 나누고 기초 구간을 점검한다.
