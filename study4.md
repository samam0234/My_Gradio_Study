# study4. 라우팅과 요청 처리

## ① 목표

주소의 쿼리로 검색어와 글 번호를 읽고, 없는 글은 오류로 보여 주며, 같은 앱의 자동 API가 어디에 생기는지 구분한다.

## ② 📖 이론

### 왜 쓰는지

Gradio 앱은 보통 주소 하나에 화면이 하나다. 탭은 그 화면 안의 구역이라 새로고침 뒤 "몇 번 글을 보고 있었는지"를 주소만으로 알 수 없다. 쿼리 문자열과 요청 객체를 읽어야 링크를 공유할 수 있다. 동시에 Gradio는 이벤트마다 API를 만들어 다른 프로그램이 화면 없이 함수를 부르게 한다.

### 핵심 개념

- **gr.Request**: 이번 호출의 헤더, 쿼리, 세션 해시를 담는다. `dict(request.query_params)`로 읽는다.
- **쿼리**: `/?q=첫&post=1`. `q`는 검색어, `post`는 글 번호다.
- **탭**: 앱 안 이동. 브라우저 경로를 바꾸지 않는다.
- **경로를 나눌 때**: 서로 다른 `Blocks`를 FastAPI에 올리려면 `gr.mount_gradio_app(app, demo, path="/board")`를 쓴다. 이 학습의 기본 실행은 앱 하나와 쿼리다.
- **오류 화면**: 없는 번호는 `gr.Error`다. HTTP 404 JSON은 게시판 API의 응답이고, 화면은 그 문장을 오류 창으로 옮긴다.
- **자동 API**: 화면 아래 Use via API. 호출 경로는 `/gradio_api/` 쪽이다. 게시판 스펙의 `/api/posts`와 다른 주소다.

### 비유

가게 문은 하나다. 전단지에 `?post=1`이라고 적혀 있으면 점원이 그 번호의 서랍을 연다. 없는 번호면 안내 벨(`gr.Error`)이 울린다. 다른 프로그램이 벨만 누르는 뒷문은 자동 API다.

## ③ 🛠️ 실기

### 전체 코드

`apps/routing_demo.py`의 핵심:

```python
def from_request(request: gr.Request):
    params = dict(request.query_params) if request else {}
    post_id = params.get("post", "")
    query = params.get("q", "")
    rows, caption = search_table(gateway, query)
    detail = "주소에 post 번호가 없습니다."
    if post_id:
        detail = post_text(gateway, int(post_id))
    return query, rows, caption, detail


def open_post(post_id: float):
    return post_text(gateway, int(post_id))
```

화면은 검색어 칸, `gr.Dataframe`, 글 번호, 상세 칸이다. `demo.load(from_request, outputs=[query, table, caption, detail])`가 열릴 때 쿼리를 읽는다. 버튼은 `open_post`를 `api_name="open_post"`로 연결하고, `ValueError`는 `gr.Error`로 올린다.

실행:

```powershell
gradio demo/study4/app.py
```

브라우저에서 `http://127.0.0.1:7860/?q=첫&post=1`을 연다. 표에는 "첫 글"이 있고 상세에 본문이 보여야 한다. `?post=99999`는 오류 창이다.

`mount_gradio_app`이 필요할 때의 형태:

```python
import gradio as gr
from fastapi import FastAPI

api = FastAPI()
api = gr.mount_gradio_app(api, demo, path="/board")
```

이 학습 앱은 루트 `launch()`로 연다. 경로를 나누는 예시는 위 세 줄로 충분하고, 게시판 JSON은 `tools/mock_api.py`가 `/api`에 따로 연다.

### 줄별 설명

- `request: gr.Request`: 인자 이름에 타입을 적으면 Gradio가 요청 객체를 넣어 준다. 입력 칸이 아니다.
- `dict(request.query_params)`: 환경에 따라 객체가 달라질 수 있어 딕셔너리로 바꾼다.
- `params.get("q", "")`: 쿼리가 없으면 전체 목록에 해당하는 빈 검색이다.
- `search_table`: 스펙의 목록 응답을 `id`, `title` 행으로 바꾼다.
- `post_text`: 상세와 댓글을 한 문자열로 만든다. 없으면 `ValueError`다.
- `int(post_id)`: 번호 칸은 숫자다. 쿼리의 `post`는 문자라 `int`로 바꾼다.
- `demo.load`: 첫 화면이 쿼리를 반영하게 한다. 버튼만 있으면 주소를 열어도 표가 비어 있다.

## ④ 🔗 연동 포인트

- 프론트의 쿼리 이름 `q`는 백엔드 `GET /api/posts?q=`와 같다. 화면 경로와 API 경로를 같은 단어로 맞춘다.
- 글 번호를 바꿀 때는 상세 탭의 번호 칸이나 `?post=`를 같이 맞춘다.
- 자동 API의 `open_post`는 Gradio 함수 호출이다. 게시판 리소스 경로는 mock 서버의 `/api/posts/{id}`다. 둘을 한 주소로 합치지 않는다.
- study6의 검색 버튼은 이 단원의 표 형식을 그대로 쓴다.

## ⑤ 오류 노트

### 쿼리를 바꿔도 화면이 그대로

- 증상: 주소만 고쳤는데 이전 검색이 남는다.
- 원인: `load`가 `request`를 받지 않거나, 브라우저가 앱 상태만 유지한다.
- 해결: 주소를 연 뒤 새로고침한다. `from_request`가 `query_params`를 읽는지 확인한다.

### `post=abc`

- 증상: `ValueError: invalid literal for int()`.
- 원인: 글 번호가 숫자가 아니다.
- 해결: 화면에서는 `gr.Error("글 번호는 숫자입니다.")`로 감싼다. API는 400 `BAD_REQUEST`다.

### 404를 성공 문장으로 표시

- 증상: 없는 글인데 빈 본문만 나온다.
- 원인: 상태 코드를 보지 않고 `data`만 읽었다.
- 해결: 200이 아니면 `format_error` 문장으로 `gr.Error`를 올린다.

## ⑥ 직접 해보기

1. `/?q=검색`으로 열어 표에 "검색 연습"만 남는지 본다.
2. `?post=1`과 없는 번호를 각각 열어 상세와 오류 창을 비교한다.
3. Use via API에서 `open_post`가 보이는지 확인하고, 그 경로가 `/api/posts`가 아님을 주소로 구분한다.

## ⑦ ☐ 체크리스트

- [ ] `gr.Request`로 `q`와 `post`를 읽는다.
- [ ] 없는 글은 `gr.Error`로 보인다.
- [ ] 탭 이동과 쿼리 이동의 차이를 설명할 수 있다.
- [ ] 자동 API 경로와 게시판 `/api` 경로를 구분했다.
- [ ] `mount_gradio_app`이 경로를 나눌 때의 함수라는 것을 안다.

## ⑧ 다음 단계

주소를 읽을 수 있는 상태에서, study5는 로그인과 글 작성 입력의 검증 문장과 중복 제출을 다룬다.
