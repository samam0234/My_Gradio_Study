# studyFinal. 심화까지 묶은 서비스

## ① 목표

study11부터 study18, 그리고 midpoint 게시판을 Gradio 하나의 앱으로 모아 저장소 설명, 외부 연동, AI, 배포 점검까지 한 주소에서 확인한다.

## ② 📖 이론

### 왜 쓰는지

단원 화면은 기능이 분리돼 있다. 최종 조립은 로그인 게시판 옆에 문서 질의와 운영 점검이 같이 있는지, 비밀과 테스트와 컨테이너가 그 앱을 깨지 않는지 보는 자리다.

### 핵심 개념

최종 앱은 새 규칙이 아니라 입구의 합이다. `apps/project_app.py`가 게시판 탭, AI 탭, 운영 탭을 한 `Blocks`에 넣는다. 루트 `app.py`가 Space와 Docker의 입구다.

### 비유

최종 점검은 같은 매장의 창고 창구, 문서 창구, 영업 일지를 한 출입문으로 여는 일이다.

## ③ 🛠️ 실기

### 기능 목록

- midpoint의 검색, 상세, 댓글, 작성, 수정, 삭제, 계정
- `DATABASE_URL` 스킴 설명. 기본 저장은 SQLite
- 문서 발췌 챗과 스트리밍, 리뷰 규칙 표시, MCP 도구 연습
- 운영 점검 JSON. 비밀 원문은 표시하지 않음
- 파일 업로드, 메일 보낸편지, 결제 링크, 모의 OAuth는 study13 화면에서 확인하고 최종 앱의 데이터 디렉터리를 공유
- Docker와 `pytest`는 배포 전에 통과

### 연동 구성도

```text
브라우저
   │
   ▼
app.py ─ launch(runtime)
   │
   ├─ 탭 게시판 ─ token State ─ BoardService ─ sqlite:///data/board.db
   │                 └─ POST_SOURCE=api 일 때 RemoteBoard ─ API_BASE_URL
   ├─ 탭 AI ─ ask_document / 모델 URL
   │         └─ analyze_review (local-rules, 사진 경로)
   │         └─ call_tool
   └─ 탭 운영 ─ describe_database, 설정 여부
환경변수: APP_ENV, DATABASE_URL, API_BASE_URL, MODEL_API_URL, GRADIO_MCP, CORS_ORIGIN
```

### 구현 순서

1. midpoint가 검색과 로그인을 통과하는지 다시 본다.
2. `describe_database`가 현재 URL을 sqlite로 설명하는지 확인한다.
3. `mount_ai`를 게시판과 같은 `Blocks`의 탭으로 넣는다. 중첩 `Blocks`를 만들지 않는다.
4. `mount_ops`를 세 번째 탭에 넣는다.
5. `python project/app.py`로 검색, 챗, 점검 버튼을 한 번씩 누른다.
6. `pytest -q`를 실행한다.
7. Dockerfile의 `CMD`가 `python app.py`인지 확인하고 공유 링크는 끈 상태로 둔다.
8. 배포한다면 study10과 study16의 점검표를 순서대로 읽는다.

`apps/project_app.py`

```python
def build() -> gr.Blocks:
    settings = load_settings()
    with gr.Blocks(title="Gradio 서비스", analytics_enabled=False) as demo:
        gr.Markdown("# Gradio 하나로 만든 게시판")
        with gr.Tab("게시판"):
            mount_board()
        with gr.Tab("AI"):
            mount_ai()
        with gr.Tab("운영"):
            mount_ops()
    return demo
```

```powershell
python project/app.py
pytest -q
```

### 배포 체크리스트

- [ ] `APP_ENV=production`이면 스택이 화면에 없다.
- [ ] `GRADIO_SHARE=false`다.
- [ ] `DATABASE_URL`의 파일이 볼륨 또는 서버에 남는다.
- [ ] `MODEL_API_KEY`, SMTP 비밀번호, OAuth 비밀이 이미지와 Git에 없다.
- [ ] `CORS_ORIGIN`이 실제 화면 주소다.
- [ ] 연습 계정 로그인, 검색, 문서 없음 답변, 점검 JSON을 한 번씩 확인했다.
- [ ] `pytest -q`가 배포 전에 통과했다.
- [ ] 백업 대상 경로를 한 줄 적었다.

### 최종 회고

다음 다섯 가지를 짧게 적는다.

1. 토큰이 상태 칸 문장에 남은 적이 있는지
2. 발췌에 없는 질문에 모델이 문장을 지어 냈는지, 그때 로컬 규칙으로 돌렸는지
3. SQLite 파일이 재시작 후에 남는지
4. Gradio 자동 API와 `/api/posts`를 혼동한 지점
5. 다음에 서버형 DB를 붙인다면 URL만 바꿀지, 저장 클래스를 새로 둘지

## ④ 🔗 연동 포인트

게시판 탭의 `open_gateway()`와 AI 탭의 `call_tool`이 같은 게이트웨이를 쓸 수 있다. 운영 탭은 게이트웨이를 열지 않고 설정만 읽는다. 모델 서버와 게시판 DB는 프로세스상 따로다. 리뷰 탭은 ReviewForge처럼 분석 결과를 자동 저장하지 않는다. 저장이 필요하면 게시판 작성 API를 사람이 또는 함수가 명시적으로 호출한다.

## ⑤ 오류 노트

### 탭 안에 화면이 비어 있음

- 증상: AI 탭이 빈 박스다.
- 원인: `build()`가 만든 `Blocks`를 다른 `Blocks` 안에 넣었다.
- 해결: `mount_ai()`처럼 컴포넌트만 만드는 함수를 탭 안에서 호출한다.

### 점검 JSON에 키가 보임

- 증상: `model_api_key` 문자열이 화면에 있다.
- 원인: 설정 딕셔너리 전체를 출력했다.
- 해결: `modelConfigured`처럼 비어 있지 않은지만 남긴다.

### 배포 후 127.0.0.1만 열림

- 증상: 컨테이너 밖에서 접속이 거절된다.
- 원인: `GRADIO_SERVER_NAME`이 루프백이다.
- 해결: 운영에서는 `0.0.0.0`이고 포트 매핑이 7860이다.

## ⑥ 직접 해보기

1. `python project/app.py`에서 게시판 검색어 `첫`의 표를 확인한다.
2. AI 탭에서 문서에 없는 질문을 넣어 없음 문장을 확인한다.
3. 운영 탭 점검 JSON에서 dialect와 `share`가 기대와 같은지 본다.

## ⑦ ☐ 체크리스트

- [ ] 게시판, AI, 운영이 한 앱의 탭이다.
- [ ] 중첩 `Blocks` 없이 `mount_*`로 조립했다.
- [ ] 배포 체크리스트를 읽었다.
- [ ] `pytest -q`가 통과했다.
- [ ] 최종 회고 다섯 줄을 적었다.
- [ ] 리뷰 결과는 자동으로 DB에 들어가지 않는다.

## ⑧ 다음 단계

이 저장소의 다음 작업은 서버형 DB를 실제로 여는 저장 클래스를 추가하거나, `MODEL_API_URL`에 발췌 지시를 지키는 모델을 연결하는 일이다. 그 전까지 기본 실행은 SQLite와 로컬 발췌다.
