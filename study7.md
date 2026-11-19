# study7. 인증·보안 기초

## ① 목표

가입, 로그인, 토큰, 작성자 확인, 비밀번호 해시, CORS, XSS와 CSRF를 Gradio 게시판에 맞춰 구분한다.

## ② 📖 이론

### 왜 쓰는지

목록은 열어 두어도 작성·수정·삭제는 누구인지 알아야 한다. 비밀번호를 그대로 저장하면 파일 유출이 곧 계정 유출이다. Gradio 화면과 게시판 API는 프로세스가 다를 수 있으므로, 로그인 상태를 브라우저 쿠키 하나에 기대지 않고 토큰으로 넘긴다.

### 핵심 개념

- **가입**: `POST /api/auth/signup`. 이메일이 있으면 409 `EMAIL_TAKEN`.
- **로그인**: `POST /api/auth/login`. 실패는 401 `INVALID_CREDENTIALS`. 이메일과 비밀번호 중 어느 쪽이 틀렸는지는 말하지 않는다.
- **토큰**: 성공 본문의 `data.accessToken`. 저장소에는 SHA-256 해시만 둔다. 화면 문장과 로그에 원문을 찍지 않는다.
- **권한**: `PATCH`와 `DELETE`는 작성자만. 아니면 403 `FORBIDDEN`.
- **해시**: `pbkdf2_hmac("sha256", ...)`. 비교는 `hmac.compare_digest`.
- **CORS**: Gradio `launch(strict_cors=True)`. API 서버는 `CORS_ORIGIN`만 허용한다. 개발 값은 `http://127.0.0.1:7860`이다.
- **XSS**: 사용자 글은 `gr.HTML`에 넣지 않는다. 상세는 `Textbox`라 태그가 실행되지 않는다.
- **CSRF**: 브라우저는 게시판 쿠키를 들고 API를 부르지 않는다. Gradio 함수가 서버에서 `Authorization: Bearer`를 붙인다. 쿠키 세션으로 바꿀 때만 CSRF 토큰이 추가로 필요하다.
- **로그아웃**: 토큰 해시를 지우고 `State`를 빈 문자열로 둔다. 204.

### 비유

비밀번호는 자물쇠 구멍에 넣는 열쇠 원문이 아니라, 열쇠를 한 방향으로만 갈아 만든 쇳가루다. 출입증(토큰)은 손님이 아니라 창구 서랍(`gr.State`)에 두고, 창고에 갈 때만 창구 직원이 들고 간다.

## ③ 🛠️ 실기

`board/security.py`

```python
def hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
```

로그인 화면 연결 `apps/board_ui.py`:

```python
token = gr.State("")
gr.Button("로그인").click(login, inputs=[email, password], outputs=[token, status])
gr.Button("로그아웃").click(lambda: ("", "로그아웃했습니다."), outputs=[token, status])
```

`login`은 `login_session`이 돌려준 원문 토큰을 `State`에만 넣고, 상태 칸에는 `닉네임 님으로 로그인했습니다.`만 쓴다. 작성 버튼의 `inputs`에 이 `token`이 들어간다.

`BoardService.login`은 해시가 맞을 때만 `insert_token(token_hash(raw), ...)`를 한다. `me`와 작성은 `_user_from_token`이 해시로 사용자를 찾는다. 만료 시각은 `TOKEN_TTL_SECONDS`이고 기본은 7일이다.

실행은 midpoint의 계정 탭이다. 연습 계정 `mina@example.com` / `password123`.

### 줄별 설명

- `secrets.token_bytes(16)`: 비밀번호마다 다른 솔트다.
- `120_000`: PBKDF2 반복 횟수. 학습용으로 고정했고, 더 낮추면 테스트는 빨라지지만 해시가 약해진다.
- `compare_digest`: 글자 비교 시간으로 힌트를 주지 않게 한다.
- `token_urlsafe`: 사용자에게 한 번 주는 원문이다.
- `sha256`: DB에 남는 값. 원문을 되돌리지 못한다.
- `gr.State("")`: 로그인 전 토큰은 빈 문자열이고, 서비스는 그때 401을 준다.
- `outputs=[token, status]`: 첫 값은 화면에 보이지 않는 상태, 둘째만 상태 칸이다.
- `strict_cors=True`: Gradio 6 `launch`의 기본에 가깝게 출처를 좁힌다.
- `CORSMiddleware(allow_origins=[origin])`: mock API가 Gradio 주소만 받는다.

## ④ 🔗 연동 포인트

- 브라우저는 Gradio와 세션으로 연결되고, Gradio 함수는 게시판 API와 Bearer 토큰으로 연결된다. 이 두 구간이 로그인 상태를 공유하는 방법이다.
- 프론트 상태 칸과 백엔드 사용자 테이블은 닉네임만 공유한다. 토큰 원문은 상태와 로그인 응답에만 잠깐 있다.
- `CORS_ORIGIN`을 바꾸면 API를 부르던 브라우저 출처도 같이 바꾼다. 포트만 바꾸면 사전 요청이 막힌다.
- study13의 모의 OAuth도 토큰을 `State`에 두는 같은 자리를 쓴다. 공급자 비밀은 `.env`다.

## ⑤ 오류 노트

### 작성만 401

- 증상: 목록은 보이고 등록만 실패한다.
- 원인: 로그인 출력이 상태 칸 문자열이라 `State`가 비어 있다.
- 해결: 로그인 `outputs`의 첫 칸을 `token` 상태로 둔다.

### 비밀번호가 응답에 있음

- 증상: 가입 응답 JSON에 해시가 있다.
- 원인: 저장 딕셔너리를 그대로 반환했다.
- 해결: `public_user`는 `id`, `email`, `nickname`만 담는다.

### 본문의 `<script>`가 실행됨

- 증상: 글 본문이 스크립트로 동작한다.
- 원인: 사용자 문자열을 `gr.HTML`에 넣었다.
- 해결: 상세는 `Textbox`를 유지한다.

### 로그인 실패 문장이 비밀번호만 지목

- 증상: "비밀번호가 틀립니다"만 나온다.
- 원인: 사용자 없음과 비밀번호 불일치를 다른 문장으로 나눴다.
- 해결: 둘 다 `INVALID_CREDENTIALS` 한 문장이다.

## ⑥ 직접 해보기

1. 계정 탭에서 연습 계정으로 로그인한 뒤 작성 탭에서 글이 201이 되는지 본다.
2. 로그아웃 후 같은 작성을 다시 눌러 401인지 확인한다.
3. 다른 이메일로 가입한 뒤 연습 계정의 글을 지우려고 해 403인지 본다.

## ⑦ ☐ 체크리스트

- [ ] 가입, 로그인, 로그아웃의 상태 코드가 201, 200, 204다.
- [ ] 비밀번호는 PBKDF2 해시로만 저장된다.
- [ ] 토큰 원문은 DB와 상태 칸 문장에 남지 않는다.
- [ ] 작성자만 수정·삭제할 수 있다.
- [ ] 사용자 본문을 `gr.HTML`에 넣지 않는다.
- [ ] `CORS_ORIGIN`과 `strict_cors`를 환경에 맞춰 두었다.
- [ ] 로그인 실패 문장이 어느 필드가 틀렸는지 나누지 않는다.

## ⑧ 다음 단계

토큰이 세션에만 있는 상태에서, study8은 이 함수들을 폴더로 나누고 개발과 운영의 `launch` 차이를 한곳에 모은다.
