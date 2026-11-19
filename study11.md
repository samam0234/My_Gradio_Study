# study11. DB 확장

## ① 목표

`DATABASE_URL` 하나로 SQLite, MariaDB, PostgreSQL, MongoDB를 구분하고, 이 저장소의 실행 경로가 어떤 SQL을 쓰는지 안다.

## ② 📖 이론

### 왜 쓰는지

학습 기본값은 파일 하나인 SQLite다. 운영에서 서버형 DB로 바꾸면 계정, 포트, 문자셋, 조인 방식이 달라진다. 화면의 `search_table`은 그대로 두고 저장 층만 바꾸려면 URL의 스킴을 먼저 읽을 수 있어야 한다.

### 핵심 개념

- **SQLite**: `sqlite:///data/board.db`. 표준 라이브러리 `sqlite3`. 서버 프로세스가 없다. 이 저장소의 `Store`가 이 파일에 `?` 바인딩으로 SQL을 보낸다.
- **PostgreSQL**: `postgresql://사용자:비밀@호스트:5432/board`. 서버가 따로 있다. 값 자리는 드라이버마다 `$1` 또는 `:name`이라 문자열 이어 붙이기로 옮기지 않는다.
- **MariaDB**: `mariadb://...` 또는 `mysql://...`. 프로토콜은 MySQL과 같고 문자셋은 `utf8mb4`다.
- **MongoDB**: `mongodb://호스트:27017/board`. 테이블 조인 대신 문서다. 댓글 수는 문서 안 숫자나 집계로 센다.
- **ORM**: SQLAlchemy를 쓰면 세션과 모델 클래스가 SQL 문자열을 대신한다. MongoDB는 그 ORM이 아니라 컬렉션 API다. 이 학습의 기본 코드는 ORM 없이 SQLite를 쓰고, URL 설명 함수만 다른 스킴을 구분한다.

### 비유

SQLite는 서랍 하나다. PostgreSQL과 MariaDB는 따로 있는 창고이고 출입증이 URL이다. MongoDB는 서류철이다. 창구(`Dataframe`)는 창고 종류를 몰라도 같은 목록 상자를 받는다.

## ③ 🛠️ 실기

`board/dburl.py`

```python
def describe_database(url: str) -> dict:
    text = (url or "").strip()
    if text.startswith("sqlite:"):
        return {"dialect": "sqlite", "driver": "stdlib sqlite3", "server": False,
                "note": "파일 하나라 학습 기본값으로 쓴다. 계정 테이블과 글 테이블을 SQL로 나눈다."}
    if text.startswith("postgres"):
        return {"dialect": "postgresql", "driver": "psycopg 또는 SQLAlchemy", "server": True,
                "note": "서버가 따로 있다. 바인딩은 드라이버마다 다르므로 SQL 문자열에 값을 붙이지 않는다."}
    if text.startswith("mysql") or text.startswith("mariadb"):
        return {"dialect": "mariadb", "driver": "PyMySQL 또는 SQLAlchemy", "server": True,
                "note": "MariaDB와 MySQL 프로토콜은 같다. 문자셋은 utf8mb4로 맞춘다."}
    if text.startswith("mongodb:") or text.startswith("mongodb+srv:"):
        return {"dialect": "mongodb", "driver": "pymongo", "server": True,
                "note": "컬렉션에 문서를 넣는다. 댓글 수는 조인 대신 문서 안 숫자나 집계로 센다."}
    return {"dialect": "unknown", "driver": "", "server": False,
            "note": "sqlite, postgresql, mariadb, mongodb 중 하나의 스킴으로 시작해야 한다."}
```

`sqlite_path`는 `sqlite:///data/board.db`를 저장소 루트의 `data/board.db`로 바꾼다. 다른 스킴은 파일을 열지 않고 설명만 돌려준다. `apps/db_demo.py`는 그 설명 JSON과, 로컬 또는 API 목록 버튼을 같이 보여 준다.

```powershell
gradio demo/study11/app.py
```

서버형 DB로 바꿀 때의 환경변수 예:

```text
DATABASE_URL=postgresql://board:비밀@db:5432/board
DATABASE_URL=mariadb://board:비밀@db:3306/board
DATABASE_URL=mongodb://db:27017/board
```

비밀은 `.env`에만 둔다. 드라이버 패키지는 그 스킴을 실제로 열 때 설치한다. 기본 테스트와 화면은 SQLite만으로 통과한다.

### 줄별 설명

- `startswith("sqlite:")`: 파일 경로 학습 경로다.
- `startswith("postgres")`: `postgresql://`와 `postgres://`를 같이 받는다.
- `mysql`과 `mariadb`: 같은 설명으로 묶는다. 문자셋 문장이 핵심이다.
- `mongodb+srv`: 호스트 이름을 DNS로 찾는 클라우드 형태다.
- `server: True`: 앱과 따로 프로세스가 있어야 한다는 표시다.
- `note`: 화면에 보여줄 차이점이다. 비밀번호는 넣지 않는다.
- `sqlite_path`: 스킴이 sqlite가 아니면 `ValueError`다. API 모드는 이 함수를 호출하지 않는다.

## ④ 🔗 연동 포인트

- 화면과 스펙 JSON은 DB가 바뀌어도 같다. 바뀌는 것은 `Store`가 여는 연결이다.
- Docker Compose를 쓸 때는 서비스 이름 `db`가 URL의 호스트가 된다. `127.0.0.1`은 컨테이너 자신을 가리킨다.
- 백업 대상이 파일인지 서버 덤프인지는 study16 점검표가 URL 스킴으로 고른다.
- `POST_SOURCE=api`이면 Gradio는 DB URL을 열지 않는다. DB는 API 서버 쪽에 있다.

## ⑤ 오류 노트

### postgres URL인데 SQLite 파일을 찾음

- 증상: `이 실행 경로는 sqlite URL만 파일로 엽니다.`
- 원인: `open_gateway`의 로컬 분기가 `sqlite_path`를 호출한다.
- 해결: 기본 학습은 sqlite URL을 유지한다. 서버형 DB를 실제로 붙일 때는 그 드라이버용 저장 클래스를 `POST_SOURCE=local` 분기에 추가하기 전에 설명 함수로 스킴만 확인한다.

### 한글이 MariaDB에서 깨짐

- 증상: 제목이 물음표다.
- 원인: 문자셋이 `utf8mb4`가 아니다.
- 해결: 데이터베이스와 연결 문자셋을 `utf8mb4`로 만든다. SQLite 파일 경로는 이 문제가 없다.

### MongoDB에 테이블 SQL을 보냄

- 증상: 드라이버가 SQL을 거절한다.
- 원인: `Store`의 `CREATE TABLE`을 그대로 보냈다.
- 해결: MongoDB는 컬렉션 `users`, `posts`, `comments`로 문서를 넣고, 목록은 스펙의 `data`/`meta`로 맞춘 뒤에 화면에 넘긴다.

## ⑥ 직접 해보기

1. `.env`를 바꾸지 않은 채 study11 화면에서 dialect가 `sqlite`인지 확인한다.
2. 설명 함수에 `postgresql://localhost/board`를 넣어 테스트가 `server is True`를 기대하는 이유를 말로 적는다.
3. MongoDB 노트 문장에서 댓글 수를 어떻게 세는지 한 줄로 적는다.

## ⑦ ☐ 체크리스트

- [ ] SQLite, PostgreSQL, MariaDB, MongoDB URL을 구분할 수 있다.
- [ ] 기본 실행과 테스트는 SQLite다.
- [ ] SQL에 비밀번호나 검색어를 이어 붙이지 않는다.
- [ ] MariaDB 문자셋은 `utf8mb4`로 적혀 있다.
- [ ] MongoDB는 조인 대신 문서와 집계라는 문장이 있다.
- [ ] 화면 목록 형식은 DB 종류와 분리돼 있다.

## ⑧ 다음 단계

저장소 종류를 설명으로 나눈 상태에서, study12는 Gradio 6의 테마와 CSS를 `launch`에 두고 입력 칸을 한 덩어리로 묶는다.
