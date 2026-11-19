# study10. 배포·정리

## ① 목표

`launch(share=True)`와 Hugging Face Spaces의 차이를 정리하고, Docker로 같은 앱을 띄우는 데 필요한 환경변수와 배포 후 점검을 목록으로 남긴다.

## ② 📖 이론

### 왜 쓰는지

내 컴퓨터의 7860은 다른 사람에게 주소가 없다. 잠시 링크만 필요하면 Gradio 공유 터널을 쓰고, 주소가 남아야 하면 Spaces나 직접 띄운 HTTPS 서버를 쓴다. 둘 다 `Blocks` 코드는 같고, 켜는 스위치와 비밀의 위치만 다르다.

### 핵심 개념

- **share=True**: `launch`가 임시 공개 주소를 만든다. 프로세스가 꺼지면 주소도 죽는다. 학습 중 화면을 보여 줄 때 쓰고, 상시 서비스의 주소로는 쓰지 않는다.
- **Hugging Face Spaces**: 저장소에 `app.py`가 있고 `requirements.txt`가 있으면 Space가 그 앱을 빌드한다. HTTPS와 도메인은 Space가 붙인다. `share=True`는 켜지 않는다.
- **Docker**: `Dockerfile`이 Python 3.12 이미지 안에서 `python app.py`를 실행한다. 포트 7860을 연다.
- **도메인**: 사람이 외우는 이름. Space는 `*.hf.space` 형태를 준다.
- **HTTPS**: 그 주소의 전송 암호화. 직접 서버에 올릴 때는 앞단의 인증서가 맡고, 앱 코드가 인증서를 직접 만들지 않아도 된다.
- **기초 정리**: study0의 설치부터 study9의 테스트까지가 한 게시판으로 이어져야 한다.

### 비유

`share=True`는 하루짜리 포장마차 주소다. Spaces는 시장이 간판과 잠금장치를 달아 주는 자리다. Docker는 포장된 주방이고, 환경변수는 그 주방에 당일 붙여 주는 재료 목록이다.

## ③ 🛠️ 실기

공유 링크는 `.env`에서만 켠다.

```text
GRADIO_SHARE=true
```

`apps/runtime.py`가 `share=settings["share"]`로 `launch`에 넘긴다. 기본값은 `false`다. 켠 뒤에는 터미널에 나온 공개 주소를 확인하고, 시연이 끝나면 `false`로 되돌리고 프로세스를 끈다.

Spaces에 올릴 파일은 루트 `app.py`와 `requirements.txt`다. `app.py`는 `project`가 아니라 최종 화면을 만들므로, Space에서도 같은 입구를 쓴다. Space의 Settings에 `APP_ENV`, `DATABASE_URL`, `GRADIO_SERVER_NAME=0.0.0.0`을 비밀 또는 변수로 넣는다. `.env` 파일 자체를 Space에 복사하지 않는다.

`Dockerfile`

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV APP_ENV=production
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_PORT=7860
ENV GRADIO_SHARE=false
EXPOSE 7860
CMD ["python", "app.py"]
```

로컬에서 이미지 동작을 보려면:

```powershell
docker build -t gradio-study .
docker run --rm -p 7860:7860 -e DATABASE_URL=sqlite:///data/board.db gradio-study
```

데이터 파일을 남기려면 `-v`로 `/app/data`를 호스트 폴더에 연결한다. 볼륨 없이 컨테이너를 지우면 SQLite도 사라진다.

### 줄별 설명

- `GRADIO_SHARE=true`: 문자 `true`만 공유를 켠다. `runtime`의 `_flag`가 `1`, `true`, `yes`, `on`을 받는다.
- `share=False`가 기본인 이유: 실수로 로컬 게시판이 공개 주소에 열리지 않게 한다.
- `FROM python:3.12-slim`: 이미지 안의 Python이다. 개발 PC가 3.10이어도 이미지 빌드는 3.12로 맞춘다.
- `COPY requirements.txt` 먼저: 소스만 바뀔 때 패키지 설치 층을 다시 쓰지 않게 한다.
- `ENV GRADIO_SHARE=false`: 컨테이너 안에서는 터널을 만들지 않는다.
- `EXPOSE 7860`: 문서용 포트 표시다. 실제로 여는 것은 `docker run -p`다.
- `CMD ["python", "app.py"]`: Space와 같은 입구다.

### 기초 구간 총정리

| 단원 | 남은 결과 |
| --- | --- |
| 0 | 가상환경, `.env`, Git 제외 |
| 1 | `Interface` 첫 응답 |
| 2 | `Blocks`, 행·열·탭, 클릭 |
| 3 | `State`, 브라우저 저장, JSON |
| 4 | 쿼리, 오류 창, 자동 API |
| 5 | 400·422, 중복 제출 |
| 6 | 스펙 v1 CRUD와 표 |
| 7 | 토큰, 해시, CORS, 텍스트 출력 |
| 8 | `apps` / `board` / `launch` |
| 9 | pytest와 mock |

## ④ 🔗 연동 포인트

- 배포 환경의 `DATABASE_URL`이 가리키는 파일 또는 서버가 앱 프로세스가 재시작돼도 남아 있어야 한다.
- `API_BASE_URL`을 쓰는 모드라면 그 호스트도 배포 네트워크에서 열려 있어야 한다. 컨테이너 안의 `127.0.0.1`은 호스트의 mock 서버가 아니다.
- `CORS_ORIGIN`은 공개 주소의 스킴과 호스트로 바꾼다. `http://127.0.0.1:7860`을 운영에 그대로 두면 브라우저 출처가 거절된다.
- HTTPS는 Space 또는 앞단 프록시가 종료한다. 앱의 `launch`에 인증서 파일을 넣지 않아도 그 구성으로 충분하다.

## ⑤ 오류 노트

### 공유 주소가 바로 죽음

- 증상: 링크가 열리다 곧 연결이 끊긴다.
- 원인: 로컬 프로세스를 종료했다. `share=True`는 그 프로세스에 붙어 있다.
- 해결: 시연 중에 프로세스를 유지한다. 남길 주소는 Spaces나 Docker다.

### Space에서 포트 오류

- 증상: Space가 앱을 죽었다고 본다.
- 원인: `server_name`이 `127.0.0.1`이라 플랫폼이 헬스 체크를 못 한다.
- 해결: `GRADIO_SERVER_NAME=0.0.0.0`과 플랫폼이 준 `PORT`를 `GRADIO_PORT`로 맞춘다.

### 재시작 후 글이 사라짐

- 증상: 컨테이너를 다시 만들면 연습 글만 있다.
- 원인: SQLite가 컨테이너 파일 시스템에만 있었다.
- 해결: 데이터 디렉터리를 볼륨에 둔다. 서버형 DB는 study11의 URL로 바꾼다.

## ⑥ 직접 해보기

1. `GRADIO_SHARE`를 켜지 않은 상태에서 터미널에 공개 주소가 없는지 확인한다.
2. `share=True`와 Spaces의 차이를 다섯 줄로 메모한다. 주소의 수명, HTTPS, 비밀의 위치, 프로세스, `app.py`를 포함한다.
3. Dockerfile의 `GRADIO_SHARE=false`를 찾아 이미지 안에서는 터널을 만들지 않는다는 문장과 연결한다.

## ⑦ ☐ 체크리스트

- [ ] `launch(share=True)` 와 Hugging Face Spaces 배포 차이 정리
- [ ] 기본 `GRADIO_SHARE`는 false다.
- [ ] Space와 Docker의 입구가 루트 `app.py`다.
- [ ] 운영 환경변수에 비밀 파일이 들어가지 않는다.
- [ ] 데이터 볼륨 또는 외부 DB 없이 재시작하면 글이 초기화된다는 것을 안다.
- [ ] 배포 후 `/`가 열리고, 로그인 후 검색 표가 나오는 것까지 확인한다.

### 배포 후 점검표

- [ ] 환경변수가 프로세스에 들어가 있다. 값은 로그에 찍지 않는다.
- [ ] `APP_ENV=production`이라 스택이 화면에 없다.
- [ ] 연습 계정으로 로그인과 검색이 된다.
- [ ] `data` 볼륨 또는 DB 연결이 재시작 후에도 남는다.
- [ ] `CORS_ORIGIN`이 실제 화면 주소다.
- [ ] `pytest -q`가 배포 전에 통과했다.

## ⑧ 다음 단계

기초 게시판을 한 번에 조립하는 문서는 `studyMidpoint.md`다. 그 다음 study11에서 저장소 종류를 바꾼다.
