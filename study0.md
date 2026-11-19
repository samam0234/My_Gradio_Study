# study0. 환경 설정

기준 버전은 Gradio 6.32.0이다. 이후 패치가 깔려도 이 단원의 명령과 폴더 이름은 같다. `gradio environment`와 `python -c "import gradio; print(gradio.__version__)"`로 설치본을 확인한다. 이 저장소를 맞춘 인터프리터는 Python 3.10.6이다.

## ① 목표

가상환경에 Gradio를 설치하고, 프로젝트 폴더에서 개발 서버를 띄워 첫 화면까지 연다.

## ② 📖 이론

### 왜 쓰는지

Gradio는 Python 함수 하나를 입력 칸과 출력 칸에 연결해 데모 화면을 만든다. ML 모델 시험, LLM 챗, 사내 테스트 도구처럼 기능 하나를 바로 보여 줄 때 잘 맞는다. Hugging Face Spaces에 앱 파일을 올리면 같은 화면을 공개 주소로 열 수 있다. 회원·게시판을 길게 키우는 일은 가능하지만, 이 프레임워크의 출발점은 "함수를 화면에 올리는 일"이다.

### 핵심 개념

- **앱**: `gr.Blocks` 또는 `gr.Interface`로 만든 화면 하나. `launch()`가 로컬 웹 서버를 연다.
- **개발 서버**: 기본 주소는 `http://127.0.0.1:7860`. `gradio app.py`는 파일을 저장하면 프로세스를 다시 시작한다.
- **컴포넌트**: 텍스트 칸, 버튼, 표처럼 화면에 놓이는 입력과 출력.
- **이벤트**: 버튼 클릭처럼 함수를 부르는 연결. 함수의 인자가 입력이고 반환값이 출력이다.
- **세션**: 브라우저 탭과 서버가 이어진 동안의 사용자 한 명. 값은 `gr.State`에 둔다. 자세한 사용은 study3.
- **환경변수**: API 주소와 비밀. `.env`에 두고 Git에는 `.env.example`만 올린다.

### 비유

함수는 조리 카드이고, 컴포넌트는 손님이 보는 접시와 주문서다. `launch()`는 그 주방을 문 연 가게다. 손님이 버튼을 누르면 카드의 함수만 다시 실행되고, 카드 전체를 처음부터 다시 읽지는 않는다. 소금 단지는 카드에 적지 않고 선반(환경변수)에 둔다.

## ③ 🛠️ 실기

### 설치와 확인 순서

PowerShell에서 프로젝트 루트로 이동한 뒤 아래 순서대로 실행한다.

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import gradio; print(gradio.__version__)"
gradio environment
```

macOS와 Linux에서는 활성화 명령만 `source .venv/bin/activate`로 바꾼다.

`python --version`은 3.10 이상을 확인한다. `python -m venv .venv`는 프로젝트 안에만 패키지를 넣는 가상환경을 만든다. `Activate.ps1` 실행 후 프롬프트에 `(.venv)`가 보여야 한다. 실행 정책 오류가 나면 현재 사용자에 대해 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`를 한 번 적용한다. `pip install -r requirements.txt`가 Gradio 6.32.0을 설치한다. `gradio environment`는 버전과 의존 패키지를 출력한다.

에디터에는 다음 확장을 둔다.

- Python (Microsoft): 인터프리터를 `.venv`로 지정한다.
- Pylance: 함수 인자와 반환 타입을 편집 중에 보여 준다.
- Ruff: 저장 시 기본 스타일을 맞춘다.

화면 확인은 브라우저가 담당한다. Gradio 전용 언어 서버는 필요 없다.

### 폴더 구조

```text
Gradio/
├── app.py                  # Spaces와 최종 실행 입구
├── apps/                   # 화면을 만드는 함수
├── board/                  # 글, 계정, 파일, 발췌 답변
├── demo/study0/app.py      # 단원별 실행 입구
├── midpoint/app.py
├── project/app.py
├── tools/mock_api.py
├── tests/
├── .env                    # Git에 올리지 않는다
├── .env.example
├── .gitignore
├── requirements.txt
└── study0.md
```

### 전체 코드

`requirements.txt`

```text
gradio==6.32.0
python-dotenv==1.1.1
requests==2.32.5
pytest==8.4.2
```

`.gitignore`

```gitignore
.venv/
__pycache__/
.pytest_cache/
.env
*.db
data/
.gradio/
```

`.env.example`

```text
APP_ENV=development
API_BASE_URL=http://127.0.0.1:8000
POST_SOURCE=local
DATABASE_URL=sqlite:///data/board.db
CORS_ORIGIN=http://127.0.0.1:7860
GRADIO_SERVER_NAME=127.0.0.1
GRADIO_PORT=7860
GRADIO_SHARE=false
GRADIO_MCP=false
```

`.env`는 `.env.example`을 복사해 만든다. 로컬 값만 적고 커밋하지 않는다.

`apps/env_demo.py`

```python
import os
from pathlib import Path

import gradio as gr

from board.config import load_settings


def build() -> gr.Blocks:
    settings = load_settings()
    with gr.Blocks(title="Gradio 환경", analytics_enabled=False) as demo:
        gr.Markdown("# Gradio 첫 화면")
        gr.Markdown("개발 서버가 이 앱을 띄웠습니다. 주소와 폴더를 확인한 뒤 다음 단원으로 갑니다.")
        gr.Textbox(label="Gradio 버전", value=gr.__version__, interactive=False)
        gr.Textbox(label="APP_ENV", value=settings["app_env"], interactive=False)
        gr.Textbox(label="작업 폴더", value=str(Path.cwd()), interactive=False)
        gr.Textbox(label="API_BASE_URL 설정됨", value=str(bool(os.getenv("API_BASE_URL"))), interactive=False)
        gr.Textbox(label="GRADIO_PORT", value=str(settings["port"]), interactive=False)
    return demo
```

개발 서버:

```powershell
gradio demo/study0/app.py
```

브라우저가 `http://127.0.0.1:7860`을 연다. 제목 "Gradio 첫 화면"과 버전 `6.32.0`이 보이면 설치와 실행이 끝난 것이다. 끝난 서버는 터미널에서 `Ctrl+C`로 중지한다. 포트가 겹치면 `.env`의 `GRADIO_PORT`를 바꾼다.

Git 저장소를 새로 만들 때:

```powershell
git init
git add .gitignore .env.example requirements.txt app.py apps board demo
git status
```

`.env`, `.venv`, `data/`가 스테이징 목록에 없으면 `.gitignore`가 동작하는 것이다.

### 줄별 설명

- `import os`: 환경변수가 있는지만 본다.
- `from pathlib import Path`: 현재 작업 폴더를 문자열로 보여 준다.
- `import gradio as gr`: 화면 함수를 `gr.`로 부른다.
- `load_settings()`: `.env`를 읽고 포트와 `APP_ENV`를 딕셔너리로 돌려준다.
- `gr.Blocks(title=...)`: 브라우저 탭 제목이 되는 화면 컨테이너다. Gradio 6에서는 테마와 CSS를 여기 두지 않고 `launch()`에 둔다.
- `analytics_enabled=False`: 사용 통계 전송을 끈다.
- `gr.Markdown`: 안내 문장이다. 비밀 값은 여기 적지 않는다.
- `gr.Textbox(..., interactive=False)`: 고칠 수 없는 표시 칸이다.
- `gr.__version__`: 설치된 Gradio 버전 문자열이다.
- `bool(os.getenv("API_BASE_URL"))`: 주소 전체가 아니라 설정 여부만 보여 준다.
- `return demo`: 실행 입구가 `launch()`에 넘길 화면이다.

`demo/study0/app.py`는 저장소 루트를 `sys.path`에 넣은 뒤 `build()`와 `launch()`를 호출한다. 루트에서 실행해야 `apps`와 `board`를 찾는다.

## ④ 🔗 연동 포인트

- Git 저장소는 학습 문서와 소스만 추적한다. `.gitignore`가 `.venv`, `.env`, `data/`, `*.db`, `.gradio/`를 제외한다.
- `API_BASE_URL`은 study6에서 게시판 API의 베이스 주소가 된다. 코드에 주소를 고정하지 않고 이 값에서 읽는다.
- `POST_SOURCE=local`이면 SQLite를 쓰고, `api`이면 `tools/mock_api.py` 같은 스펙 서버를 부른다.
- `GRADIO_PORT`와 `CORS_ORIGIN`은 화면 주소와 API가 서로를 알아볼 때 맞춘다.
- 개발 서버를 띄운 상태가 study1의 자동 새로고침과 브라우저 개발자도구 확인의 출발점이다.

## ⑤ 오류 노트

### `gradio`를 찾을 수 없음

- 증상: `gradio : 'gradio' 용어가 cmdlet 이름이 아닙니다`.
- 원인: 가상환경이 꺼져 있다.
- 해결: `.\.venv\Scripts\Activate.ps1` 후 `python -m gradio environment`로 확인한다.

### 포트 7860이 이미 사용 중

- 증상: 서버가 뜨지 않거나 이전 화면이 그대로다.
- 원인: 이전에 띄운 `launch()`가 남아 있다.
- 해결: 그 터미널에서 `Ctrl+C`로 중지한다. 다른 번호가 필요하면 `GRADIO_PORT`를 바꾼다.

### `ModuleNotFoundError: apps`

- 증상: `demo/study0/app.py`를 다른 폴더에서 실행했는데 `apps`를 못 찾는다.
- 원인: 스크립트 폴더가 모듈 경로의 맨 앞이 된다.
- 해결: 저장소 루트에서 실행한다. 실행 입구가 루트를 `sys.path`에 넣는다.

### `.env`를 읽지 않음

- 증상: 포트를 바꿨는데 7860이 그대로다.
- 원인: `.env`가 루트가 아니거나, 서버를 다시 시작하지 않았다.
- 해결: 루트의 `.env`를 저장한 뒤 프로세스를 다시 띄운다. `load_dotenv`는 프로세스 시작 때 읽는다.

## ⑥ 직접 해보기

1. 가상환경을 지운 뒤 이 단원의 명령만 보고 다시 설치하고 `gradio environment`의 버전 줄을 메모한다.
2. `.env`의 `GRADIO_PORT`를 7862로 바꾼 뒤 서버를 다시 띄워 주소가 바뀌는지 확인한다.
3. `git status`에 `.env`와 `data/`가 없는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] Python 3.10 이상을 `python --version`으로 확인했다.
- [ ] `.venv`를 만들고 활성화한 뒤 그 환경에 패키지를 설치했다.
- [ ] `gradio environment` 또는 `import gradio`로 6.32 계열인지 확인했다.
- [ ] `apps/`, `board/`, `demo/`, `requirements.txt`, `.env.example` 자리를 만들었다.
- [ ] Python, Pylance, Ruff 확장을 설치하고 인터프리터를 `.venv`로 지정했다.
- [ ] `.gitignore`에 `.venv/`, `.env`, `data/`, `*.db`, `.gradio/`가 있다.
- [ ] `.env.example`을 복사해 `.env`를 만들었고, Git 상태에 `.env`가 보이지 않는다.
- [ ] 앱, 컴포넌트, 이벤트, 세션, 환경변수라는 용어를 한 줄씩 설명할 수 있다.

## ⑧ 다음 단계

첫 화면이 브라우저에 뜬 상태에서, study1은 `gr.Interface`로 이름과 주제를 받아 첫 응답 문장을 만들고 개발자도구로 서버와의 연결을 확인한다.
