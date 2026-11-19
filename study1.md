# study1. Hello World와 기본 문법

## ① 목표

`gr.Interface`로 첫 응답 문장을 만들고, 저장할 때 개발 서버가 앱을 다시 띄우는 과정을 브라우저에서 확인한다.

## ② 📖 이론

### 왜 쓰는지

환경이 준비된 뒤에는 "함수 하나가 화면에 어떻게 붙는가"를 먼저 고정해야 한다. Gradio의 문법은 HTML 템플릿 문자가 아니라 Python 함수와 컴포넌트다. `gr.Interface(fn, inputs, outputs)`는 그 함수의 인자 순서와 반환값을 입력 칸, 출력 칸에 맞춘다.

### 핵심 개념

- **fn**: 화면이 부를 Python 함수. 인자 개수는 `inputs` 길이와 같다.
- **inputs / outputs**: 컴포넌트 또는 `"text"` 같은 짧은 이름. 이 단원은 컴포넌트를 직접 만들어 라벨을 붙인다.
- **f-string**: 위젯 값을 문장에 섞는 Python 문법이다. Gradio 전용 중괄호 템플릿은 없다.
- **examples**: 함수에 넣어 볼 인자 목록. 방문자 예제를 클릭하면 `fn`이 한 번 돈다.
- **api_name**: 이 함수를 다른 프로그램이 부를 때의 이름. 화면 아래 API 문서에 나타난다.
- **파일 저장 시 재시작**: `gradio demo/study1/app.py`가 저장을 감지하면 프로세스를 다시 시작한다.

### 비유

`Interface`는 창구가 하나인 매장이다. 주문서(`inputs`)를 내면 조리 함수(`fn`)가 완성 접시(`outputs`)만 내놓는다. 매장 안 자리 배치를 바꾸려면 study2의 `Blocks`로 간다.

## ③ 🛠️ 실기

### 전체 코드

`apps/hello.py`

```python
import gradio as gr


def greet(name: str, topic: str) -> str:
    who = (name or "").strip() or "방문자"
    picked = topic or "출력"
    return f"{who}님, 오늘은 {picked}을 봅니다."


def build() -> gr.Interface:
    return gr.Interface(
        fn=greet,
        inputs=[
            gr.Textbox(label="이름", value="방문자"),
            gr.Dropdown(choices=["출력", "입력", "이벤트"], label="오늘 볼 것", value="출력"),
        ],
        outputs=gr.Textbox(label="응답"),
        title="안녕하세요, Gradio",
        description="함수 반환값이 화면의 응답입니다.",
        examples=[["민아", "출력"]],
        api_name="greet",
        analytics_enabled=False,
    )
```

실행:

```powershell
gradio demo/study1/app.py
```

브라우저 확인:

1. 주소가 `http://127.0.0.1:7860`인지 본다.
2. 개발자도구를 연다. Windows에서는 `F12`다.
3. Network 탭에서 첫 문서 요청이 200인지 본다. 버튼을 누른 뒤 `/gradio_api/`로 시작하는 호출이 추가되면 함수 호출이 서버로 간 것이다.
4. `greet`의 문장을 저장해 고친다. `gradio` 명령으로 띄웠다면 서버가 다시 시작되고 브라우저를 새로고침하면 문장이 바뀐다.
5. Console에 빨간 예외가 없는지 본다. Python 예외는 터미널에도 나온다.

### 줄별 설명

- `def greet(name, topic)`: 입력 칸 두 개의 현재 값을 받는다.
- `(name or "").strip() or "방문자"`: `None`과 공백을 방문자로 바꾼다.
- `return f"..."`: 이 문자열이 출력 칸의 값이 된다.
- `gr.Interface`: 함수, 입력, 출력을 한 번에 묶는 첫 데모 형태다.
- `gr.Textbox`: 한 줄 또는 여러 줄 문자 칸. `value`는 처음 값이다.
- `gr.Dropdown`: 목록 중 하나를 고른다. `choices`가 선택지다.
- `outputs=gr.Textbox`: 반환 문자열을 보여줄 칸이다.
- `title`, `description`: 화면 위 제목과 설명이다.
- `examples=[["민아", "출력"]]`: `greet`의 인자 순서와 같은 리스트다.
- `api_name="greet"`: 자동 API에서 이 함수의 이름이다.
- `analytics_enabled=False`: 사용 통계를 끈다.

## ④ 🔗 연동 포인트

- `gradio` 명령의 파일 감시가 이 단원의 자동 새로고침이다. `python demo/study1/app.py`는 저장해도 프로세스를 갈아끼우지 않는다.
- 브라우저 Network의 `/gradio_api/` 호출이 다음 단원에서 이벤트 함수로 이어진다. 화면이 직접 게시판 DB를 열지 않고, 함수가 서버에서 일한다.
- `api_name`은 study4와 study18에서 다른 프로그램, MCP 도구가 같은 함수를 부를 때 쓰는 이름이다.

## ⑤ 오류 노트

### 입력 개수와 인자 개수가 다름

- 증상: 제출 직후 `TypeError` 또는 입력 칸이 비어 보임.
- 원인: `inputs` 길이와 `greet` 인자 수가 다르다.
- 해결: 칸 하나당 인자 하나로 맞춘다. 반환값이 하나면 `outputs`도 하나다.

### 예제 클릭이 실패함

- 증상: Examples를 누르면 예외가 난다.
- 원인: `examples`의 안쪽 리스트 길이가 입력 개수와 다르다.
- 해결: `["민아", "출력"]`처럼 입력 순서 그대로 둔다.

### 저장해도 문장이 안 바뀜

- 증상: 파일을 고쳤는데 이전 문장이 남는다.
- 원인: `python`으로 띄워 감시가 없거나, 브라우저가 이전 탭을 보고 있다.
- 해결: `gradio demo/study1/app.py`로 다시 띄우고 브라우저를 새로고침한다.

## ⑥ 직접 해보기

1. 예제 "민아 / 출력"을 눌러 응답 문장이 함수 반환값과 같은지 확인한다.
2. 드롭다운을 "이벤트"로 바꾸고 제출한 뒤 Network에 API 호출이 추가되는지 본다.
3. `api_name`을 `hello`로 바꾼 뒤 화면 아래 Use via API 문서의 이름이 바뀌는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `gr.Interface(fn, inputs, outputs)` 로 첫 데모
- [ ] 반환 문자열이 출력 칸에 보이는지 확인했다.
- [ ] f-string으로 입력값을 문장에 섞었다.
- [ ] `gradio` 명령으로 띄운 뒤 저장과 새로고침으로 문장 변경을 확인했다.
- [ ] 개발자도구 Network에서 `/gradio_api/` 호출을 보았다.
- [ ] `examples` 한 줄이 함수 인자 순서와 같다.

## ⑧ 다음 단계

첫 응답이 보인 상태에서, study2는 `gr.Blocks`로 행·열·탭을 나누고 버튼 클릭에 함수를 직접 연결한다.
