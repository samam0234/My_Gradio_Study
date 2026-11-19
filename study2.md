# study2. 핵심 구조

## ① 목표

`gr.Blocks`로 행, 열, 탭을 나누고, 버튼 클릭이 어떤 함수를 어떤 칸에 연결하는지 직접 만든다.

## ② 📖 이론

### 왜 쓰는지

`Interface`는 입력 묶음 하나와 출력 묶음 하나에 잘 맞는다. 검색 칸과 결과 표를 나란히 두거나, 설명 탭을 따로 두려면 자리를 직접 짜야 한다. Gradio의 기본 단위는 블록 안의 컴포넌트이고, 단위끼리의 데이터는 이벤트 함수의 인자와 반환값으로 오간다.

### 핵심 개념

- **Blocks**: `with gr.Blocks()` 안에서 컴포넌트를 만든 뒤, 그 객체를 이벤트에 넘긴다.
- **Row / Column**: 가로는 `Row`, 세로는 `Column`이다. 안에 `with`로 들어간다.
- **Tab**: 같은 앱 안의 화면 나눔이다. 브라우저 주소를 바꾸지는 않는다.
- **click**: `button.click(fn, inputs, outputs)`. `inputs`의 현재 값이 `fn` 인자로 들어가고, 반환값이 `outputs`에 채워진다.
- **gr.Error**: 함수 안에서 올리면 화면 위 오류 창이 된다. 반환값으로 처리하지 않은 실패를 여기서 보여 준다.
- **api_name**: 이 클릭을 자동 API의 한 엔드포인트로 연다.

### 비유

`Blocks`는 매장 도면이고, `Row`와 `Column`은 계산대와 진열대의 자리다. 버튼은 벨이다. 벨을 누르면 도면 전체를 다시 그리지 않고, 벨에 적어 둔 함수만 주문서와 진열대를 주고받는다.

## ③ 🛠️ 실기

### 전체 코드

`apps/blocks_layout.py`

```python
import gradio as gr


def shout(message: str) -> tuple[str, str]:
    text = (message or "").strip()
    if not text:
        raise gr.Error("문구를 입력하세요.")
    return text.upper(), f"길이 {len(text)}"


def build() -> gr.Blocks:
    with gr.Blocks(title="Blocks 레이아웃", analytics_enabled=False) as demo:
        gr.Markdown("# 입력 열과 출력 열")
        with gr.Tab("변환"):
            with gr.Row():
                with gr.Column():
                    message = gr.Textbox(label="문구")
                    button = gr.Button("변환", variant="primary")
                with gr.Column():
                    upper = gr.Textbox(label="결과")
                    meta = gr.Textbox(label="부가")
            button.click(shout, inputs=message, outputs=[upper, meta], api_name="shout")
        with gr.Tab("설명"):
            gr.Markdown("탭은 이 화면 안의 구역이다. 주소 경로로 나누는 법은 study4에서 다룬다.")
    return demo
```

실행은 `gradio demo/study2/app.py`다.

### 줄별 설명

- `def shout`: 문구 하나를 받아 결과 둘을 돌려준다.
- `raise gr.Error`: 빈 입력을 출력 칸에 넣지 않고 오류 창으로 올린다.
- `return text.upper(), f"길이 ..."`: 튜플의 순서가 `outputs` 리스트 순서와 같다.
- `with gr.Blocks() as demo`: 이 블록 안에서 만든 컴포넌트만 이 화면에 속한다.
- `with gr.Tab("변환")`: 첫 탭. 이름표가 탭 버튼이 된다.
- `with gr.Row()` / `with gr.Column()`: 왼쪽 입력, 오른쪽 출력.
- `variant="primary"`: 강조 버튼 색이다.
- `button.click(...)`: 클릭 때만 `shout`가 돈다. 칸에 글자를 타이핑하는 동안에는 함수가 돌지 않는다.
- `inputs=message`: 컴포넌트 객체다. 문자열 라벨이 아니다.
- `outputs=[upper, meta]`: 반환값 두 칸.
- `api_name="shout"`: 다른 프로그램이 이 변환을 부를 때 쓰는 이름이다.

ReviewForge 데모도 이 구조다. `gr.Interface` 대신 `Blocks`로 왼쪽 입력 열과 오른쪽 출력 열을 두고, `button.click(run, inputs=[...], outputs=[...])`로 잇는다. 잘못된 입력은 `raise gr.Error(...)`로 화면에 올린다.

## ④ 🔗 연동 포인트

- 컴포넌트 변수(`message`, `upper`)가 단위 사이의 계약이다. 함수는 화면 객체를 몰라도 되고, `click`이 값을 건넨다.
- 반환 튜플의 순서를 바꾸면 결과 칸과 부가 칸이 바뀐다. 다음 단원의 `gr.State`도 이 출력 목록에 넣을 수 있다.
- `api_name`이 붙은 클릭은 study14의 자동 API와 study18의 MCP 도구 후보가 된다.

## ⑤ 오류 노트

### 출력 개수 불일치

- 증상: 클릭 후 값이 한 칸만 바뀌거나 예외가 난다.
- 원인: `return` 개수와 `outputs` 길이가 다르다.
- 해결: 칸이 둘이면 값을 둘 돌려준다. 하나만 필요하면 리스트도 하나다.

### 블록 밖에서 컴포넌트를 만듦

- 증상: 칸이 화면에 없거나 다른 앱에 붙는다.
- 원인: `Textbox`를 `with gr.Blocks()` 밖에서 만들었다.
- 해결: 칸 생성은 해당 `with` 안으로 옮긴다.

### 탭이 주소가 된다고 착각

- 증상: 탭을 눌렀는데 URL의 경로가 안 바뀐다.
- 원인: `Tab`은 이 페이지 안의 구역이다.
- 해결: 주소와 쿼리는 study4에서 `gr.Request`로 읽는다.

## ⑥ 직접 해보기

1. 빈 문구로 변환을 눌러 오류 창 문장을 확인한다.
2. 오른쪽 열의 출력 순서를 일부러 바꿔 보고, 어느 칸에 대문자가 들어가는지 맞춘다.
3. 설명 탭에 오늘 만든 `api_name`을 한 줄 적는다.

## ⑦ ☐ 체크리스트

- [ ] `gr.Blocks` 로 레이아웃(행·열·탭)과 이벤트(`btn.click`) 직접 구성
- [ ] 입력 열과 출력 열을 `Row`와 `Column`으로 나눴다.
- [ ] 빈 입력에 `gr.Error`가 뜬다.
- [ ] 반환 튜플 순서와 `outputs` 순서가 같다.
- [ ] `api_name`을 이벤트에 붙였다.

## ⑧ 다음 단계

자리와 클릭이 연결된 상태에서, study3은 그 클릭이 끝난 뒤에도 남을 값과 파일에 남길 값을 나눈다.
