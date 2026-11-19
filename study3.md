# study3. 데이터 다루기

## ① 목표

한 번의 클릭을 넘어 유지할 값, 브라우저에 남길 값, 파일에 남길 값을 각각 다른 자리에 둔다.

## ② 📖 이론

### 왜 쓰는지

이벤트 함수의 지역 변수는 그 호출이 끝나면 사라진다. 이번 탭에서 저장한 횟수, 이 브라우저가 기억하는 이름, 서버를 껐다 켜도 남을 메모는 수명이 다르다. 수명을 섞으면 새로고침 뒤에 횟수가 남거나, 반대로 메모가 사라진다.

### 핵심 개념

- **gr.State**: 서버가 이 세션에 대해 기억하는 값. 화면 칸이 아니다. 입력과 출력 양쪽에 넣어 함수가 읽고 다시 돌려준다.
- **gr.BrowserState**: 브라우저 저장소에 남는 값. `storage_key`가 키다. 로그인 토큰처럼 비밀은 여기 두지 않는다.
- **JSON 파일**: `data/notes.json`. 프로세스와 브라우저가 둘 다 끝나도 남는다.
- **바인딩**: Gradio는 칸을 변수에 자동으로 묶지 않는다. `click`이나 `load`의 `inputs`와 `outputs`가 묶음이다.
- **load**: 페이지가 열릴 때 한 번 도는 이벤트. 파일에 있던 메모를 칸에 채울 때 쓴다.

### 비유

`State`는 계산대가 손에 쥔 전표다. 손님이 나가면 전표도 닫힌다. `BrowserState`는 손님 지갑의 메모지다. JSON 파일은 가게 서랍이다. 전표에 적힌 비밀번호를 지갑에 옮기지 않는다.

## ③ 🛠️ 실기

### 전체 코드

`board/notes.py`

```python
import json
from pathlib import Path


def load_notes(path: Path) -> list[dict]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else []


def save_note(path: Path, nickname: str, text: str, at: str) -> list[dict]:
    notes = load_notes(path)
    notes.append({"nickname": nickname.strip() or "익명", "text": text.strip(), "at": at})
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
    return notes
```

`apps/state_demo.py`의 연결:

```python
count = gr.State(0)
nickname = gr.BrowserState("방문자", storage_key="gradio-study-nickname")
button.click(remember, inputs=[text, name, count], outputs=[count, board, nickname, text])
demo.load(load_existing, inputs=nickname, outputs=[name, board])
```

`remember`는 메모가 비어 있으면 `gr.Error`를 올리고, 아니면 파일에 한 줄 추가한 뒤 횟수에 1을 더해 `count`로 돌려준다. 표시 이름은 `nickname` 출력으로 브라우저에 다시 쓴다. 메모 칸은 빈 문자열로 비운다.

실행은 `gradio demo/study3/app.py`다. 저장 위치는 `data/notes.json`이다.

### 줄별 설명

- `load_notes`: 파일이 없으면 빈 리스트다. JSON이 리스트가 아니면 그것도 빈 리스트로 본다.
- `notes.append`: 한 번의 저장이 딕셔너리 하나다. 닉네임, 문장, 시각을 같이 둔다.
- `path.parent.mkdir`: `data/`가 없어도 만든다.
- `ensure_ascii=False`: 한글을 `\u` 이스케이프 없이 파일에 쓴다.
- `gr.State(0)`: 처음 횟수는 0이다. 새로고침하면 이 세션 값은 다시 0에서 시작한다.
- `gr.BrowserState`: 같은 `storage_key`가 있으면 그 값을 처음 값보다 우선한다.
- `inputs=[text, name, count]`: 칸 둘과 상태 하나. 함수 인자 순서와 같다.
- `outputs`의 `count`: 새 횟수를 상태에 다시 넣는다. 이 출력이 없으면 다음 클릭도 0이다.
- `demo.load`: 열릴 때 파일과 브라우저 이름을 칸에 채운다.

## ④ 🔗 연동 포인트

- 화면 칸은 이번 이벤트의 입력이다. 오래 둘 글은 파일이고, 나중에는 study6의 SQLite다.
- 로그인 토큰은 `State`에만 둔다. `BrowserState`에는 표시 이름처럼 비밀이 아닌 값만 둔다. study7이 이 구분을 그대로 쓴다.
- `data/`는 `.gitignore`에 있다. 메모 파일은 저장소에 올라가지 않는다.

## ⑤ 오류 노트

### 횟수가 항상 1

- 증상: 저장할 때마다 횟수가 1이다.
- 원인: `count`를 `outputs`에 넣지 않아 상태가 갱신되지 않는다.
- 해결: 입력과 출력 모두에 같은 `gr.State`를 둔다.

### JSON이 깨짐

- 증상: 다음 실행에서 `JSONDecodeError`.
- 원인: 파일을 저장하는 중에 프로세스가 끊겼거나 손으로 고치다 쉼표를 빼먹었다.
- 해결: 그 파일만 지우고 다시 저장한다. 학습 데이터이므로 복구 대상이 아니다.

### 이름가 토큰을 같이 넣음

- 증상: 브라우저 저장소를 열어 보니 토큰이 있다.
- 원인: `BrowserState`에 인증 값을 넣었다.
- 해결: 토큰은 서버 세션의 `State`로 옮기고 브라우저 키는 비운다.

## ⑥ 직접 해보기

1. 메모를 두 번 저장하고 횟수가 2가 되는지 본다. 새로고침 뒤 횟수는 0이고 파일의 두 줄은 남는지 확인한다.
2. 표시 이름을 바꾼 뒤 브라우저를 새로 열고 `storage_key`의 값이 다시 채워지는지 본다.
3. `data/notes.json`을 열어 한글이 그대로 있는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `gr.State`를 입력과 출력에 모두 넣어 횟수가 누적된다.
- [ ] `gr.BrowserState`에는 비밀이 아닌 표시 이름만 둔다.
- [ ] 메모가 `data/notes.json`에 한 줄씩 쌓인다.
- [ ] 새로고침 후 횟수는 리셋되고 파일 내용은 남는다.
- [ ] 빈 메모는 `gr.Error`로 막힌다.

## ⑧ 다음 단계

파일과 세션이 나뉜 상태에서, study4는 주소의 쿼리로 검색어와 글 번호를 읽어 목록과 상세를 연다.
