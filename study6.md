# study6. DB·API 연동

## ① 목표

환경변수로 고른 저장소에 대해 검색, 상세, 등록, 수정, 삭제를 만들고, 검색 결과는 `gr.Dataframe`에 올린다.

## ② 📖 이론

### 왜 쓰는지

데모 함수 안의 리스트는 서버를 재시작하면 사라진다. 게시판은 공통 스펙의 경로와 JSON을 지켜야 나중에 화면만 남겨 두고 저장소를 바꿀 수 있다. Gradio는 DB 드라이버가 아니다. 화면 함수가 `BoardService` 또는 HTTP 클라이언트를 부른다.

### 핵심 개념

- **연결**: `POST_SOURCE=local`이면 `DATABASE_URL`의 SQLite 파일. `api`이면 `API_BASE_URL`.
- **모델**: 사용자, 글, 댓글, 토큰 해시. 화면으로 나가는 글에는 비밀번호 해시가 없다.
- **목록**: `GET /api/posts?q=&page=&limit=&sort=`. 응답은 `data` 배열과 `meta`다.
- **상세**: `GET /api/posts/{id}`. `body`, `tags`, `author`, `commentCount`, 시각이 있다.
- **등록**: `POST /api/posts`. 201과 `Location`은 HTTP 서버가 붙인다.
- **수정**: `PATCH /api/posts/{id}`. 보낸 필드만 바꾼다.
- **삭제**: `DELETE`. 204이고 본문이 없다.
- **오류**: 404 `NOT_FOUND`, 403 `FORBIDDEN`, 401 `UNAUTHORIZED`.

### 비유

Gradio는 창구이고, 서비스는 창고 관리 장부다. 창구는 "검색어"를 장부에 넘기고, 장부는 규격 상자(`data`, `meta`)를 돌려준다. 창고가 옆 건물(API)이어도 상자 모양은 같다.

## ③ 🛠️ 실기

연결은 `board/gateway.py`의 `open_gateway()`가 한다. 로컬은 `BoardService(Store(sqlite_path(...)))`이고, API 모드는 `RemoteBoard`다.

목록을 표로 바꾸는 함수 `board/present.py`:

```python
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
```

화면 `apps/board_ui.py`의 검색 탭:

```python
query = gr.Textbox(label="검색어")
page = gr.Number(label="쪽", value=1, precision=0)
table = gr.Dataframe(
    headers=["id", "title"],
    datatype=["number", "str"],
    type="array",
    label="결과",
)
caption = gr.Textbox(label="목록 정보", interactive=False)
gr.Button("검색").click(search, inputs=[query, page], outputs=[table, caption], api_name="search_posts")
```

상세, 작성, 수정, 삭제, 댓글은 같은 파일의 탭이다. 작성은 `create_message`, 수정은 `update_message`, 삭제는 `delete_message`다. 모두 토큰 `gr.State`를 입력으로 받는다.

실행은 `python midpoint/app.py`다. 검색어 `첫`을 넣으면 표에 `1`과 `첫 글`이 나오고, 목록 정보는 `검색어 첫 · 1건 · 1/1쪽`이다.

API만 따로 보려면:

```powershell
python tools/mock_api.py
```

그리고 `.env`에 `POST_SOURCE=api`를 둔 뒤 Gradio를 다시 띄운다. mock 서버는 8000이고 Gradio는 7860이다.

### 줄별 설명

- `gateway.list_posts`: 로컬이든 HTTP든 같은 인자다. `q`, `page`, `limit`.
- `status != 200`: 표에 오류 JSON을 억지로 넣지 않고 예외로 올린다.
- `rows`: `gr.Dataframe(type="array")`가 받는 리스트의 리스트다. 노션의 최소 예제와 같이 `id`, `title` 두 칸이다.
- `meta`: `page`, `limit`, `total`, `totalPages`, `q`. 화면에는 한 줄 설명으로만 보여 준다.
- `datatype`: 열 형식. 번호 열과 문자 열을 구분한다.
- `api_name="search_posts"`: 검색 이벤트의 API 이름이다.
- `headers=["id", "title"]`: 표 머리글. 스펙의 필드 이름과 같다.

로컬 `create_post`는 검증 뒤에 `insert_post`를 하고 201과 상세 `data`를 돌려준다. `delete_post`는 작성자가 아니면 403, 없으면 404, 성공이면 204와 `None`이다.

## ④ 🔗 연동 포인트

- 베이스 주소와 저장 파일은 환경변수다. 함수 안에 `http://localhost:8000`을 적지 않는다.
- 검색 쿼리 `q`는 study4의 주소 쿼리, mock 서버의 쿼리, 표의 캡션이 같은 이름이다.
- 작성 본문 키는 `body`다. `content`로 보내지 않는다.
- 201의 `Location` 헤더는 `tools/mock_api.py`가 HTTP에서 붙인다. 화면은 본문의 `data.id`를 쓴다.
- 다음 단원의 토큰이 있어야 등록·수정·삭제가 200번대가 된다. 목록과 상세는 토큰 없이 읽는다.

## ⑤ 오류 노트

### 표가 비고 오류도 없음

- 증상: 검색 후 머리글만 있다.
- 원인: `type="array"`가 아닌데 리스트를 넘겼거나, 검색어가 어떤 제목·본문에도 없다.
- 해결: `type="array"`를 확인하고 검색어를 비운 뒤 전체 목록을 본다.

### API 모드에서만 실패

- 증상: 로컬은 되고 `POST_SOURCE=api`만 503이다.
- 원인: mock 서버가 꺼져 있거나 포트가 `API_BASE_URL`과 다르다.
- 해결: `http://127.0.0.1:8000/health`가 `{"status":"ok"}`인지 본다.

### 남의 글 삭제가 됨

- 증상: 다른 계정 토큰으로 204가 난다.
- 원인: `authorId` 비교를 빠뜨렸다.
- 해결: `delete_post`의 403 분기를 유지한다. 테스트 `test_crud_permissions`가 이 경우를 고정한다.

## ⑥ 직접 해보기

1. `midpoint`에서 검색어 `첫`의 표와 캡션을 확인한다.
2. 상세 탭에서 글 번호 1을 열어 본문 "안녕하세요"와 태그를 본다.
3. mock 서버를 띄우고 `POST_SOURCE=api`로 같은 검색이 되는지 비교한 뒤 다시 `local`로 되돌린다.

## ⑦ ☐ 체크리스트

- [ ] 게시판 API 호출: 검색어 입력 → 결과 표(`gr.Dataframe`)
- [ ] 연결 정보가 `API_BASE_URL`, `DATABASE_URL`, `POST_SOURCE`에 있다.
- [ ] 목록 응답에 `data`와 `meta`가 있다.
- [ ] 상세·등록·수정·삭제의 상태 코드가 200, 201, 204, 403, 404로 갈린다.
- [ ] 응답에 비밀번호 해시가 없다.
- [ ] 작성 JSON의 본문 키는 `body`다.

## ⑧ 다음 단계

CRUD가 상태 코드로 구분되는 상태에서, study7은 그 중 인증이 필요한 요청이 토큰을 어떻게 실어 보내는지와 비밀번호를 어떻게 저장하는지를 다룬다.
