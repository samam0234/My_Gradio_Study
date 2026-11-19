# study5. 폼·입력·검증

## ① 목표

이메일, 비밀번호, 제목, 본문을 받아 검증하고, 실패 문장을 보여 주며, 같은 제출이 겹치면 거절한다.

## ② 📖 이론

### 왜 쓰는지

버튼에 함수만 연결하면 빈 제목도 저장될 수 있다. 사용자는 어느 칸이 잘못됐는지 문장으로 봐야 하고, 느린 저장 중에 버튼을 두 번 눌러 글이 두 개 생기면 안 된다. Gradio에는 HTML form 태그가 따로 없다. 입력 칸과 버튼, 그리고 함수 안의 검증이 폼이다.

### 핵심 개념

- **검증 함수**: `validate_post`가 필드 이름과 메시지 목록을 만든다. 제목은 1~200자, 본문은 1~5000자다.
- **400**: 스펙 v1의 검증 실패. 본문은 `error.code = VALIDATION_ERROR`, `error.fields`다.
- **422**: 어떤 API는 같은 실패를 422로 준다. 화면은 400과 422를 같은 필드 표시로 받는다. 이 저장소의 로컬 서비스는 400을 쓴다.
- **401**: 로그인 전 작성. 토큰이 없으면 글을 만들지 않는다.
- **중복 제출**: `concurrency_limit=1`로 그 버튼의 동시 실행을 하나로 제한하고, 같은 토큰의 잠금이 이미 잡혀 있으면 429 문장을 돌려준다.
- **gr.Error**: 상태 문장 전체를 오류 창에 올린다. 필드별 문장이 그 안에 들어 있다.

### 비유

폼은 창구 서류다. 빈 칸이 있으면 서류가 서랍에 들어가지 않고 어느 칸인지 도장이 찍혀 돌아온다. 같은 서류가 두 장 겹치면 두 번째는 잠시 거절한다.

## ③ 🛠️ 실기

### 전체 코드

`apps/form_demo.py`

```python
def submit(email: str, password: str, title: str, body: str):
    try:
        token, hello = login_session(gateway, email, password)
        created = create_message(gateway, token, title, body, "form")
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    return f"{hello}\n{created}"
```

버튼:

```python
gr.Button("제출", variant="primary").click(
    submit,
    inputs=[email, password, title, body],
    outputs=result,
    concurrency_limit=1,
    api_name="submit_post",
)
```

`create_message`는 같은 토큰으로 이미 작성이 진행 중이면 `429 RATE_LIMITED` 문장으로 `ValueError`를 낸다. 검증 실패는 `400 VALIDATION_ERROR`와 `title: 1~200자로 입력하세요.` 같은 줄이다.

실행은 `gradio demo/study5/app.py`다. 연습 계정은 `mina@example.com` / `password123`다.

원격 API가 422와 FastAPI `detail` 배열을 주면 `RemoteBoard`가 `error.fields`로 바꾼다.

```python
if response.status_code == 422 and "error" not in payload:
    return 422, error_body("VALIDATION_ERROR", "입력값을 확인하세요.", fields)
```

### 줄별 설명

- `login_session`: 이메일과 비밀번호로 토큰과 인사 문장을 만든다. 실패하면 `ValueError`다.
- `create_message`: 토큰으로 글을 만든다. 제목과 본문을 스펙의 `title`, `body`로 보낸다.
- `except ValueError`: 서비스 문장을 오류 창으로 옮긴다. 토큰 원문은 문장에 없다.
- `return f"{hello}\n{created}"`: 201일 때만 결과 칸에 글 번호가 들어간다.
- `concurrency_limit=1`: 이 버튼의 함수가 동시에 두 개 돌지 않게 큐가 줄 세운다.
- `api_name="submit_post"`: 화면 없이 같은 검증을 부를 때의 이름이다.

화면이 상태 코드별로 하는 일:

| 코드 | 화면 |
| --- | --- |
| 200, 201 | 결과 칸에 성공 문장. 토큰은 `State`에만 있고 이 칸에는 없다. |
| 400, 422 | 오류 창에 `error.message`와 필드 문장 |
| 401 | 로그인 실패 또는 토큰 없음 |
| 429 | 이전 제출이 끝나기 전에 다시 누름 |

## ④ 🔗 연동 포인트

- 입력 칸의 값은 함수 인자로만 서버에 간다. 브라우저는 게시판 DB를 직접 열지 않는다.
- 로컬 모드는 `BoardService`가 400을 만든다. `POST_SOURCE=api`이면 `RemoteBoard`가 같은 함수 이름으로 HTTP를 보내고, 422를 필드 오류로 정규화한다.
- 성공 토큰은 study7에서 `gr.State`로 옮겨 다음 작성 요청의 `Authorization` 헤더가 된다. 이 단원의 폼은 제출 한 번 안에서 로그인과 작성을 이어서 한다.

## ⑤ 오류 노트

### 빈 제목인데 글이 생김

- 증상: 제목 없이 201이 난다.
- 원인: `validate_post`를 지나치지 않는 다른 함수로 저장했다.
- 해결: `create_post`만 저장 입구로 쓴다. 테스트 `test_signup_validation_and_duplicate`가 필드 문장을 고정한다.

### 버튼을 두 번 눌렀는데 글이 둘

- 증상: 같은 제목의 글이 두 개다.
- 원인: 잠금 없이 `create_post`를 두 스레드가 통과했다.
- 해결: `create_message`의 토큰 잠금과 버튼 `concurrency_limit=1`을 같이 둔다.

### 422인데 필드가 안 보임

- 증상: `detail` 배열만 있고 화면에는 일반 실패로 나온다.
- 원인: 원격 응답을 `error.fields`로 바꾸기 전에 본문을 그대로 보여 줬다.
- 해결: `RemoteBoard`의 422 분기를 탄다. 로컬 서비스는 처음부터 400과 `fields`를 준다.

## ⑥ 직접 해보기

1. 제목을 비우고 제출해 `title: 1~200자로 입력하세요.`가 오류 창에 있는지 본다.
2. 연습 계정으로 제목과 본문을 채워 201과 글 번호가 결과 칸에 나오는지 확인한다.
3. 잘못된 비밀번호로 제출해 401 문장이 이메일만 또는 비밀번호만 지목하지 않는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 빈 제목은 400 `VALIDATION_ERROR`와 필드 문장으로 막힌다.
- [ ] 422도 같은 필드 표시로 받는 분기가 있다.
- [ ] 성공 문장에 토큰 원문이 없다.
- [ ] 버튼에 `concurrency_limit=1`이 있다.
- [ ] 겹친 제출은 429 문장으로 거절된다.
- [ ] 글 본문 키는 `body`다.

## ⑧ 다음 단계

검증을 통과한 작성만 남는 상태에서, study6은 검색 표를 포함해 목록·상세·등록·수정·삭제를 스펙 v1에 맞춘다.
