# study8. 구조화·재사용

## ① 목표

화면, 게시판 규칙, 실행 설정을 폴더로 나누고, 개발과 운영에서 바뀌는 값만 환경변수로 남긴다.

## ② 📖 이론

### 왜 쓰는지

검색 함수와 해시 함수와 `launch` 인자가 한 파일에 있으면 포트를 바꿀 때마다 화면 코드를 고치게 된다. 같은 목록 변환을 midpoint와 성능 실험이 같이 쓰려면 함수가 화면 밖에 있어야 한다.

### 핵심 개념

- **apps/**: Gradio 컴포넌트와 이벤트만 둔다.
- **board/**: 검증, 저장, HTTP, 파일, 메일을 둔다. Gradio를 import하지 않는 모듈이 테스트의 대상이다.
- **demo/, midpoint/, project/**: `sys.path`에 루트를 넣고 `build()`를 `launch()`한다. 로직을 복사하지 않는다.
- **config.py**: `.env`를 한 번 읽어 딕셔너리로 준다.
- **개발**: `APP_ENV=development`, `show_error=True`, `GRADIO_SERVER_NAME=127.0.0.1`, `GRADIO_SHARE=false`.
- **운영**: `APP_ENV=production`, `show_error=False`, 서버 이름 `0.0.0.0`, 공유 링크는 끈다. 오류 원문은 로그에만 남긴다.

### 비유

주방(`board`)과 홀(`apps`)을 나눈다. 영업일 안내문(`APP_ENV`)만 문 앞에 붙이고, 레시피는 영업일이 바뀌어도 같은 서랍에 둔다.

## ③ 🛠️ 실기

`apps/runtime.py`

```python
def launch(demo: gr.Blocks) -> None:
    configure_logging()
    settings = load_settings()
    production = settings["app_env"] == "production"
    demo.launch(
        server_name=settings["server_name"],
        server_port=settings["port"],
        share=settings["share"],
        theme=gr.themes.Soft(),
        css=".gradio-container { max-width: 980px !important; margin: auto; }",
        strict_cors=True,
        show_error=not production,
        mcp_server=settings["mcp"],
        inbrowser=False,
    )
```

폴더가 맡은 일:

| 경로 | 역할 |
| --- | --- |
| `board/config.py` | 환경변수 |
| `board/service.py` | 스펙과 같은 상태 코드 |
| `board/present.py` | 표와 문장 |
| `apps/board_ui.py` | 게시판 탭 |
| `apps/runtime.py` | `launch` |
| `demo/studyN/app.py` | 그 단원 실행 |
| `midpoint/app.py` | 기초 게시판 실행 |
| `project/app.py` | 최종 실행 |

개발에서 화면을 볼 때는 `.env`의 `APP_ENV=development`다. Docker 이미지는 `APP_ENV=production`과 `GRADIO_SERVER_NAME=0.0.0.0`을 이미지 환경으로 넣는다. 비밀은 이미지에 복사하지 않고 실행할 때 넘긴다.

### 줄별 설명

- `configure_logging`: 표준 출력에 시각과 수준을 붙인다. study9와 study16이 이 형식을 본다.
- `production`: 문자 `production`만 운영으로 본다. 오타가 나면 개발로 남는다.
- `server_name`, `port`, `share`: 코드 상수가 아니라 설정이다.
- `show_error=not production`: 개발은 예외를 화면에 보여주고, 운영은 숨긴다.
- `mcp_server`: study18에서 켤 스위치다. 기본은 꺼져 있다.
- `theme`, `css`: Gradio 6에서는 `Blocks()`가 아니라 `launch()` 인자다.

## ④ 🔗 연동 포인트

- 개발 PC의 `.env`와 운영 컨테이너의 환경변수는 같은 키를 쓴다. 값만 다르다.
- `DATABASE_URL`이 파일을 가리키면 그 경로는 컨테이너 볼륨과 맞춰야 재시작 후에도 글이 남는다. study10과 study11이 이 경로를 이어받는다.
- 화면 파일은 `open_gateway()`만 부른다. SQLite와 HTTP의 분기는 `board/gateway.py` 한곳이다.

## ⑤ 오류 노트

### 운영인데 스택이 화면에 보임

- 증상: 배포 주소에서 Python traceback이 보인다.
- 원인: `APP_ENV`가 `production`이 아니어서 `show_error`가 켜져 있다.
- 해결: 환경변수를 확인하고 프로세스를 다시 띄운다.

### 설정을 화면 파일에 하드코딩

- 증상: 포트가 7860으로 고정돼 있다.
- 원인: `launch(server_port=7860)`을 앱 파일에 다시 적었다.
- 해결: 실행 입구는 `apps.runtime.launch`만 쓴다.

### 순환 import

- 증상: `board`가 `apps`를 import하다 실패한다.
- 원인: 저장 모듈이 화면을 불러 왔다.
- 해결: `board`는 Gradio를 모르는 상태로 둔다. 예외 메시지 문자열만 올리고, `gr.Error`는 `apps`에서 감싼다.

## ⑥ 직접 해보기

1. `board/present.py`의 캡션 문장을 한 글자 바꾸고 midpoint만 다시 띄워 검색 캡션이 바뀌는지 본다.
2. `.env`의 `APP_ENV`를 `production`으로 둔 뒤 일부러 없는 글을 열어 화면의 예외 상세가 줄어드는지 본다. 본 뒤 `development`로 되돌린다.
3. `apps` 안에서 `sqlite3.connect`를 직접 호출하는 곳이 없는지 검색한다.

## ⑦ ☐ 체크리스트

- [ ] 화면은 `apps/`, 규칙은 `board/`, 실행은 `demo`·`midpoint`·`project`로 나뉘어 있다.
- [ ] `launch` 인자는 `runtime.py` 한곳에 있다.
- [ ] 개발과 운영의 차이가 `APP_ENV`, `GRADIO_SERVER_NAME`, `show_error`로 설명된다.
- [ ] 비밀과 DB 파일은 이미지와 Git에 없다.
- [ ] 같은 목록 변환을 화면 둘 이상이 import할 수 있다.

## ⑧ 다음 단계

폴더가 나뉜 상태에서, study9는 `board` 함수를 pytest로 고정하고 API 호출은 가짜 응답으로 바꾼다.
