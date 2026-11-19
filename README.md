# Gradio 학습

함수를 입력·출력 컴포넌트에 연결해 ML 데모, 챗 화면, 사내 시험 도구를 만드는 Gradio 학습 기록이다. 기준 버전은 Gradio 6.32.0이다. 이 저장소를 확인한 인터프리터는 Python 3.10.6이고, 설치 명령은 Python 3.10 이상에서 같다. 설명은 `study*.md`에 있고, 실행 코드는 `demo/`, `midpoint/`, `project/`와 루트 `app.py`에 있다.

노션 페이지: [Gradio](https://app.notion.com/p/40bd7dec5e2e817d80f6c0d5b92decbc)

게시판이 주고받는 JSON은 [HTTP · REST · API 설계](https://app.notion.com/p/3d6d7dec5e2e8139adbfd36dd506c65e)의 `/api` 스펙 v1이다. 글 본문 키는 `body`다.

## 문서

| 파일 | 내용 |
| --- | --- |
| `study0.md` | 설치, 폴더, 개발 서버, Git, `.env` |
| `study1.md` | `gr.Interface` 첫 응답 |
| `study2.md` | `gr.Blocks`, 행·열·탭, `click` |
| `study3.md` | `gr.State`, 브라우저 저장, JSON 파일 |
| `study4.md` | 쿼리, 탭, 오류 화면, 자동 API |
| `study5.md` | 검증, 400·422, 중복 제출 |
| `study6.md` | 스펙 v1 CRUD와 `gr.Dataframe` |
| `study7.md` | 로그인, 해시, CORS, XSS·CSRF |
| `study8.md` | 폴더와 개발·운영 설정 |
| `study9.md` | pytest, mock, 자주 나는 오류 |
| `study10.md` | `share=True`, Spaces, Docker |
| `studyMidpoint.md` | 기초만으로 만드는 작은 게시판 |
| `study11.md` | SQLite, MariaDB, PostgreSQL, MongoDB |
| `study12.md` | 테마, CSS, 입력 묶음 |
| `study13.md` | 업로드, 메일, 결제 링크, OAuth |
| `study14.md` | REST, OpenAPI, 페이지, 오류 형식 |
| `study15.md` | 캐시, 비동기, 측정 |
| `study16.md` | Actions, 로그, 백업 점검표 |
| `study17.md` | 타이머 알림, 파일 처리 |
| `study18.md` | 챗, 스트리밍, MCP, DocuForge·ReviewForge |
| `studyFinal.md` | 심화까지 묶은 서비스 |

## 실행

저장소 루트에서 설치한다.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

기본값은 `POST_SOURCE=local`이다. 글과 계정은 `data/board.db`에 생긴다. 연습 계정은 `mina@example.com` / `password123`이다.

```powershell
gradio demo/study1/app.py
python midpoint/app.py
python project/app.py
python app.py
pytest -q
```

`gradio 파일.py`는 저장할 때 프로세스를 다시 띄운다. `python 파일.py`는 한 번만 실행한다.

| 실습 | 명령 |
| --- | --- |
| study0 | `gradio demo/study0/app.py` |
| study1 | `gradio demo/study1/app.py` |
| study2 | `gradio demo/study2/app.py` |
| study3 | `gradio demo/study3/app.py` |
| study4 | `gradio demo/study4/app.py` |
| study5 | `gradio demo/study5/app.py` |
| study6~10, midpoint | `python midpoint/app.py` |
| study11 | `gradio demo/study11/app.py` |
| study12 | `gradio demo/study12/app.py` |
| study13 | `gradio demo/study13/app.py` |
| study14 | `gradio demo/study14/app.py` |
| study15 | `gradio demo/study15/app.py` |
| study16 | `gradio demo/study16/app.py` |
| study17 | `gradio demo/study17/app.py` |
| study18 | `gradio demo/study18/app.py` |
| final | `python project/app.py` |
| API 연습 서버 | `python tools/mock_api.py` |

API 모드로 바꾸려면 `.env`의 `POST_SOURCE=api`로 두고 mock 서버를 먼저 띄운다. 기본 포트는 Gradio 7860, API 8000이다. 테스트는 `pytest -q`다.

## 읽는 순서

`study0.md`에서 환경을 만든 뒤 번호 순서대로 읽는다. `studyMidpoint.md`는 `study10.md` 다음에, `studyFinal.md`는 `study18.md` 다음에 읽는다.

`.env`는 커밋하지 않는다. 모델 키, SMTP 비밀번호, OAuth 클라이언트 비밀도 같은 파일에만 둔다.
