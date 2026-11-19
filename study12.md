# study12. 프론트·UI 연동

## ① 목표

Gradio 6에서 테마와 CSS를 어디에 두는지 정하고, 입력 칸과 버튼을 한 묶음으로 다룬다.

## ② 📖 이론

### 왜 쓰는지

기능이 통해도 칸이 화면 가득 늘어지면 어디가 입력인지 보이지 않는다. Gradio의 화면 층은 컴포넌트와 테마다. 상태도 별도의 저장 라이브러리 없이 `gr.State`와 이벤트 출력이 맡는다. 폼도 별도 패키지 없이 칸과 버튼과 검증 함수다.

### 핵심 개념

- **테마**: `launch(theme=gr.themes.Soft())`. Gradio 6에서는 `Blocks()` 생성자가 아니라 `launch` 인자다.
- **CSS**: `launch(css=...)`. 본문 폭을 980px로 두는 규칙이 `runtime.py`에 있다.
- **상태**: 입력 도중에 서버가 모든 칸을 다시 그리지 않는다. 버튼 출력이 지정한 칸만 바뀐다.
- **폼**: `Textbox`와 `Dropdown`, `Button`을 `Column`에 모으고, 클릭 함수가 검증한다.
- **클라이언트**: 다른 Python 프로세스는 `gradio_client`로 `api_name`을 부른다. 그 호출도 이 앱의 함수다.

### 비유

테마는 매장 조명이고 CSS는 통로 폭이다. 조명을 `launch`라는 개점 스위치에 달아 두었으므로, 조리 카드(`Blocks` 안 함수)를 고칠 때 조명을 다시 배선하지 않는다.

## ③ 🛠️ 실기

`apps/runtime.py`의 개점 인자:

```python
demo.launch(
    theme=gr.themes.Soft(),
    css=".gradio-container { max-width: 980px !important; margin: auto; }",
)
```

`apps/theme_demo.py`

```python
with gr.Row():
    with gr.Column():
        name = gr.Textbox(label="이름")
        color = gr.Dropdown(choices=["Soft", "Default", "Glass"], label="테마 이름", value="Soft")
    with gr.Column():
        out = gr.Textbox(label="적용 메모")
gr.Button("메모").click(
    lambda n, c: f"{(n or '방문자').strip()} 화면은 {c} 테마 설명을 보고 있습니다.",
    inputs=[name, color],
    outputs=out,
)
```

실행은 `gradio demo/study12/app.py`다. 실제로 칠해지는 테마는 드롭다운 문자열이 아니라 `runtime.launch`의 `gr.themes.Soft()`다. 드롭다운은 그 사실을 문장으로 확인하는 입력이다.

다른 프로세스에서 같은 함수를 부를 때:

```python
from gradio_client import Client
client = Client("http://127.0.0.1:7860")
client.predict("민아", "출력", api_name="/greet")
```

study1을 띄운 뒤에만 이 호출이 성공한다. 예측 경로의 이름은 `api_name`과 같다.

### 줄별 설명

- `theme=gr.themes.Soft()`: 색과 모서리의 기본 세트다.
- `css=...`: 한 줄 규칙이다. 사용자 글의 HTML을 넣는 자리가 아니다.
- `max-width: 980px`: 넓은 모니터에서 칸이 끝에서 끝까지 늘어지지 않게 한다.
- `gr.Row` / `gr.Column`: 입력 묶음과 결과 묶음이다.
- `lambda`: 학습용 한 줄 함수다. 검증이 필요하면 `board`의 함수로 뺀다.
- `Client`: 브라우저 대신 Python이 이벤트를 누른다. 화면 코드를 복사하지 않는다.

## ④ 🔗 연동 포인트

- midpoint와 project도 `runtime.launch`를 타므로 같은 테마와 폭을 쓴다. 화면 파일마다 테마를 다시 적지 않는다.
- `gr.State`는 study3과 study7의 토큰 자리다. UI 단원에서 두 번째 상태 저장소를 만들지 않는다.
- `gradio_client`는 자동 API가 떠 있는 동안에만 연결된다. 서버를 끄면 클라이언트도 끊긴다.

## ⑤ 오류 노트

### `Blocks(theme=...)`가 무시됨

- 증상: 테마를 블록에 넣었는데 색이 기본이다.
- 원인: Gradio 6은 테마를 `launch`에서 받는다.
- 해결: `apps/runtime.py`만 수정한다.

### CSS에 사용자 문장을 넣음

- 증상: 글 제목이 스타일 시트로 들어간다.
- 원인: 제목을 f-string으로 `css`에 섞었다.
- 해결: CSS는 고정 문자열이다. 사용자 값은 컴포넌트 출력으로만 보낸다.

### Client가 404

- 증상: `api_name`을 찾을 수 없다.
- 원인: 서버가 다른 앱이거나 이름이 `/greet`가 아니다.
- 해결: 화면 아래 API 문서의 이름과 `predict`의 `api_name`을 맞춘다.

## ⑥ 직접 해보기

1. study12 화면에서 이름과 테마 이름을 제출해 결과 문장을 확인한다.
2. `runtime.py`의 CSS 폭 숫자를 찾고, 그 값이 블록 생성자가 아니라 `launch`에 있음을 말한다.
3. study1을 띄운 뒤 API 문서에 `greet`가 있는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 테마와 CSS가 `launch` 인자다.
- [ ] 입력 칸과 버튼이 `Row`/`Column`으로 묶여 있다.
- [ ] 상태는 `gr.State`와 이벤트 출력으로 충분하다.
- [ ] 사용자 문자열이 CSS에 들어가지 않는다.
- [ ] `gradio_client`는 `api_name`으로 같은 함수를 부른다.

## ⑧ 다음 단계

화면 폭과 테마가 한곳에 모인 상태에서, study13은 파일, 사진, 메일, 결제 링크, 모의 소셜 로그인을 각각의 탭으로 붙인다.
