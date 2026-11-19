# studyMidpoint. 기초만으로 만드는 작은 게시판

## ① 목표

study0부터 study10까지 배운 Gradio만으로 로그인과 CRUD가 되는 작은 게시판을 한 앱으로 조립한다.

## ② 📖 이론

### 왜 쓰는지

단원마다 화면이 따로 있으면 검색은 되는데 로그인한 작성은 다른 앱에 남는다. 중간 조립은 "한 주소에서 검색, 상세, 작성, 수정, 삭제, 계정"이 이어지는지 확인하는 자리다. 새 라이브러리를 더하지 않는다.

### 핵심 개념

기능은 기초 단원의 조합이다. 표는 study6, 토큰은 study7, 검증은 study5, 실행 스위치는 study8과 study10이다.

### 비유

중간 점검은 연습 경기다. 새로운 전술을 넣지 않고, 지금까지의 동작이 한 경기에 붙는지 본다.

## ③ 🛠️ 실기

### 기능 목록

- 연습 계정 로그인, 가입, 로그아웃
- 검색어와 쪽 번호로 목록을 `gr.Dataframe`에 표시
- 글 번호로 본문과 댓글 보기, 댓글 등록
- 로그인 사용자의 글 등록, 수정, 삭제
- 빈 제목은 400, 남의 글은 403, 없는 글은 404
- 저장은 로컬 SQLite. `POST_SOURCE=api`이면 같은 화면이 HTTP를 호출

### 폴더 구조

```text
midpoint/app.py          # 실행 입구
apps/midpoint_app.py     # Blocks 하나
apps/board_ui.py         # 탭과 이벤트
board/                   # 스펙, SQLite, HTTP
.env                     # POST_SOURCE, DATABASE_URL, API_BASE_URL
```

### 단계별 구현 순서

1. study0의 가상환경과 `.env`를 만든다.
2. `board/store.py`와 `board/service.py`로 사용자·글·댓글을 SQLite에 둔다.
3. `board/present.py`로 목록을 행과 캡션으로 바꾼다.
4. `apps/board_ui.py`에 검색, 상세, 작성, 수정·삭제, 계정 탭을 둔다.
5. 로그인 출력을 `gr.State`에 넣고 작성·수정·삭제의 입력으로 연결한다.
6. `python midpoint/app.py`로 열고 검색어 `첫`을 확인한다.
7. `pytest -q`로 권한과 검증을 고정한다.
8. 보여줄 때만 `GRADIO_SHARE=true`를 잠깐 켠다.

### DB·API 연동 구성도

```text
브라우저 127.0.0.1:7860
        │  Gradio 세션
        ▼
apps/board_ui.py  ──token State──►  board/present.py
                                        │
                    POST_SOURCE=local   │  POST_SOURCE=api
                                        ▼
                                 BoardService          RemoteBoard
                                        │                  │
                                        ▼                  ▼
                                 data/board.db      API_BASE_URL/api
```

### 전체 코드

실행 입구 `midpoint/app.py`는 루트를 경로에 넣은 뒤 `apps.midpoint_app.build`를 `launch`한다. 화면은 다음이 전부다.

```python
import gradio as gr
from apps.board_ui import mount_board

def build() -> gr.Blocks:
    with gr.Blocks(title="Gradio 게시판", analytics_enabled=False) as demo:
        mount_board()
    return demo
```

`mount_board`가 탭과 `token = gr.State("")`를 만든다. 검색 버튼은 `search_table`을 `gr.Dataframe`에 연결하고 `api_name="search_posts"`를 붙인다. 계정 탭의 로그인은 토큰과 상태 문장을 나누어 반환한다.

```powershell
python midpoint/app.py
```

연습 계정은 `mina@example.com` / `password123`이다.

### 1차 배포 체크리스트

- [ ] `.env`가 Git에 없다.
- [ ] `POST_SOURCE`와 `DATABASE_URL`이 실행 환경과 같다.
- [ ] 검색, 로그인, 작성, 로그아웃 후 작성 거절을 한 번씩 확인했다.
- [ ] `pytest -q`가 통과했다.
- [ ] 공개 링크를 썼다면 시연 후 프로세스를 종료했다.
- [ ] 재시작 후 글이 남아야 하면 DB 파일 위치를 적었다.

### 회고

잘 된 점과 막힌 점을 다섯 줄로 적는다. 예시 질문: 토큰을 상태 칸에 찍은 적이 있는가, 검색 쿼리 이름이 API와 같았는가, 빈 제목 문장이 필드 이름을 포함하는가. 심화에서 바꿀 것은 여기 적고 study11 전에 코드로 먼저 넣지 않는다.

## ④ 🔗 연동 포인트

이 앱의 `open_gateway()`가 이후 모든 화면의 저장 입구다. study11은 URL의 뜻만 넓히고, study14는 같은 목록 계약을 OpenAPI로 적는다. mock 서버를 쓸 때는 API를 먼저 8000에 띄우고 Gradio를 그다음에 띄운다.

## ⑤ 오류 노트

### 탭은 보이는데 검색이 비어 있음

- 증상: 머리글만 있다.
- 원인: 검색 버튼을 누르지 않았거나 SQLite 시드가 다른 파일을 보고 있다.
- 해결: `DATABASE_URL`의 파일을 확인하고 검색어를 비운 뒤 버튼을 누른다. 시드 글은 "첫 글"과 "검색 연습"이다.

### 로그인했는데 작성이 401

- 증상: 상태 칸에는 닉네임이 있는데 작성만 실패한다.
- 원인: 로그인 이후 `.then`이 상태 문장만 갱신하고, 작성 함수가 빈 토큰을 읽는다.
- 해결: 작성 `inputs`의 첫 값이 `token` 상태인지 본다. 로그아웃은 그 상태를 빈 문자열로 돌려야 한다.

## ⑥ 직접 해보기

1. 검색어 `첫`으로 표와 캡션을 확인한다.
2. 로그인 후 글을 하나 만들고, 상세에서 본문을 연 뒤 삭제한다.
3. 로그아웃 후 같은 번호 삭제가 거절되는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 기능 목록의 검색, 상세, 작성, 수정, 삭제, 계정이 한 앱에 있다.
- [ ] 새 프레임워크 패키지를 더하지 않았다.
- [ ] 연습 계정으로 로그인 CRUD를 한 바퀴 돌았다.
- [ ] 1차 배포 체크리스트를 시연 전에 읽었다.
- [ ] 회고를 다섯 줄 적었다.

## ⑧ 다음 단계

기초 게시판이 한 주소에서 동작하면, study11은 `DATABASE_URL`의 스킴을 MariaDB, PostgreSQL, MongoDB로 바꿨을 때 무엇이 달라지는지 적고 기본 실행은 SQLite로 유지한다.
