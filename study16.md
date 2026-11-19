# study16. 운영·CI/CD

## ① 목표

테스트를 자동으로 돌리고, 컨테이너로 띄우며, 로그와 백업을 배포 전에 점검표로 확인한다.

## ② 📖 이론

### 왜 쓰는지

로컬에서 한 번 통과한 테스트는 다음 커밋에서 깨질 수 있다. 이미지를 만드는 절차와 로그 위치, 백업 대상이 목록으로 남아 있어야 다른 날 같은 순서로 확인할 수 있다.

### 핵심 개념

- **Docker**: study10의 `Dockerfile`. 운영 환경변수는 이미지 밖이다.
- **GitHub Actions**: `.github/workflows/ci.yml`이 push와 pull request마다 `pytest -q`를 실행한다.
- **로그**: `runtime.configure_logging`이 표준 출력에 남긴다. 컨테이너는 그 출력을 모은다.
- **모니터링**: study16 화면의 점검 버튼이 환경 이름, 포트, DB 종류, 파일 존재, 모델·SMTP 설정 여부만 JSON으로 보여 준다.
- **백업**: SQLite는 `data/board.db` 복사다. 서버형 DB는 그 서버의 덤프다. `data/uploads`도 같이 복사해야 파일이 남는다.

### 비유

CI는 문을 열기 전에 저울을 재는 점원이다. Docker는 포장된 주방이고, 로그는 영업 일지다. 백업은 서랍 복사본이다. 일지에 열쇠 번호를 적지 않는다.

## ③ 🛠️ 실기

`.github/workflows/ci.yml`

```yaml
name: test
on:
  push:
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - run: pip install -r requirements.txt
      - run: pytest -q
```

점검 화면은 `gradio demo/study16/app.py`다. 버튼이 `ops_report`를 호출한다. 비밀 값 원문은 JSON에 넣지 않고, 모델 주소와 SMTP 호스트가 비어 있지 않은지만 `true`/`false`로 적는다.

백업 명령의 예:

```powershell
Copy-Item data\board.db data\board-backup.db
```

복사본도 `data/` 안이라 Git에 올라가지 않는다. 운영에서는 이 파일을 앱 서버 밖 디스크로 옮긴다.

### 줄별 설명

- `on.push`: 브랜치에 커밋이 올라갈 때 돈다.
- `setup-python`: CI의 Python이다. 이 저장소 확인 버전인 3.10과 맞춘다.
- `pip install -r requirements.txt`: Gradio와 pytest를 설치한다.
- `pytest -q`: study9와 같은 명령이다. 실패하면 머지 전에 고친다.
- `ops_report`: 프로세스 환경의 요약이다. 화면을 새로고침해도 비밀이 보이지 않아야 한다.
- `sqliteExists`: 파일을 한 번도 안 만들었으면 false다. midpoint를 한 번 띄우면 true가 된다.
- `Copy-Item`: 앱이 파일을 쓰는 중이면 복사본이 반쪽일 수 있다. 점검은 트래픽이 없는 때에 한다.

### 점검표

- [ ] `pytest -q`가 로컬에서 통과했다.
- [ ] Actions 파일이 `requirements.txt`와 같은 테스트를 실행한다.
- [ ] Docker 실행 명령에 `.env` 파일을 이미지 안에 넣지 않는다.
- [ ] 로그 형식에 토큰, 비밀번호, API 키가 없다.
- [ ] 점검 JSON에 비밀 원문이 없다.
- [ ] SQLite 또는 덤프와 `uploads`의 백업 위치를 한 줄로 적었다.
- [ ] 복구 연습으로 백업 파일을 다른 폴더의 `DATABASE_URL`에 연결해 글이 보이는지 한 번 확인했다.

## ④ 🔗 연동 포인트

- CI는 DB 서버를 띄우지 않는다. 테스트가 임시 SQLite와 mock만 쓰기 때문이다. 운영 DB 비밀번호를 Actions 기본 변수에 넣지 않는다.
- 배포 워크플로를 나중에 추가하면 테스트 잡이 성공한 뒤에만 이미지를 만든다. 이 단원은 테스트 잡까지다.
- 점검 화면의 `database.dialect`는 study11 설명과 같은 함수다.
- 백업 파일의 경로는 운영 노트의 `DATABASE_URL`과 같아야 복구가 된다.

## ⑤ 오류 노트

### Actions만 실패

- 증상: 로컬 pytest는 되는데 CI가 설치에서 죽는다.
- 원인: `requirements.txt`에 없는 패키지를 로컬 가상환경에만 설치했다.
- 해결: 그 패키지를 requirements에 버전과 함께 적거나 import를 제거한다.

### 로그에 토큰이 남음

- 증상: 표준 출력에 `accessToken`이 보인다.
- 원인: 로그인 응답 전체를 `logger.info`했다.
- 해결: 상태 코드와 사용자 번호만 남긴다.

### 백업이 비어 있음

- 증상: 복사한 db를 열면 시드만 있다.
- 원인: 다른 `DATABASE_URL`의 파일을 복사했다.
- 해결: 점검 JSON이 가리키는 경로와 복사 대상을 맞춘다.

## ⑥ 직접 해보기

1. `pytest -q`를 실행해 CI와 같은 명령이 통과하는지 본다.
2. study16 화면의 점검 결과에서 `modelConfigured`와 `smtpConfigured`가 false인지 확인한다.
3. `data/board.db`가 있다면 백업 복사본을 만들고 Git 상태에 나타나지 않는지 본다.

## ⑦ ☐ 체크리스트

- [ ] 위 점검표의 항목을 배포 전에 읽는다.
- [ ] Actions는 `pytest -q`만 자동 실행한다.
- [ ] Docker와 비밀 주입 위치가 분리돼 있다.
- [ ] 로그와 점검 JSON에 비밀 원문이 없다.
- [ ] 백업 대상이 SQLite 파일과 업로드 폴더임을 말할 수 있다.

## ⑧ 다음 단계

배포 전 목록이 있는 상태에서, study17은 알림 파일을 몇 초마다 다시 읽고 텍스트 파일의 줄 수를 세는 확장을 붙인다.
