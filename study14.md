# study14. API 설계

## ① 목표

게시판 REST 계약과 Gradio 자동 API를 문서로 구분하고, 페이지와 오류 본문 규칙을 화면에서 확인한다.

## ② 📖 이론

### 왜 쓰는지

화면 버튼 이름만 있으면 다른 프로그램이 무엇을 보내야 하는지 모른다. 경로, 버전, 페이지, 오류 모양을 적어 두면 저장소와 화면을 따로 고쳐도 계약이 남는다. Gradio는 그와 별도로 이벤트 API 문서를 만든다. 둘을 한 문서로 섞으면 `/api/posts`와 `/gradio_api`가 뒤섞인다.

### 핵심 개념

- **자원**: 복수 명사 `/api/posts`, `/api/posts/{id}`. 동사 경로는 쓰지 않는다.
- **버전**: 이 학습의 계약 이름은 v1이다. 경로에 `/v1`을 넣지 않고 문서 `info.version`에 `1.0.0`을 적는다. 호환을 깨는 변경은 문서를 먼저 올린다.
- **페이지**: `page`는 1부터, `limit` 기본 10, 최대 50. `meta.totalPages`를 같이 준다.
- **정렬**: `sort=-createdAt`이 기본이다. 허용 값만 `ORDER BY`에 넣는다.
- **오류**: `error.code`, `error.message`, `error.fields`, `error.requestId`. 스택은 넣지 않는다.
- **OpenAPI**: `board/openapi_spec.py`의 딕셔너리. mock 서버는 `/api-docs`에 대화형 문서를 연다.
- **Gradio 문서**: 화면 아래 Use via API. 이벤트 `api_name`이 항목이다.

### 비유

REST 문서는 창고 창구의 서류 양식이다. Gradio 문서는 매장 벨의 이름표다. 양식과 이름표를 한 클립에 묶지 않는다.

## ③ 🛠️ 실기

`board/openapi_spec.py`의 `board_openapi()`는 `/health`, `/api/posts`, `/api/posts/{id}`와 200, 201, 400, 401, 403, 404를 적는다.

`apps/api_demo.py`는 그 JSON을 `gr.Code(language="json")`으로 보여 주고, `q`와 `page`로 `search_table`을 부른다. 버튼 이름은 `GET /api/posts`이고 `api_name="list_posts"`다.

```powershell
gradio demo/study14/app.py
```

페이지를 2로 두고 글이 둘뿐이면 표는 비고 캡션의 쪽 수가 맞아야 한다. `page`에 0을 넘기는 서비스 경로는 400 `BAD_REQUEST`다. 화면 숫자는 1부터 시작한다.

오류 예:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값을 확인하세요.",
    "fields": { "title": ["1~200자로 입력하세요."] },
    "requestId": "..."
  }
}
```

### 줄별 설명

- `openapi: 3.0.3`: 문서 형식 버전이다. 게시판 계약 버전과 숫자가 달라도 된다.
- `info.version`: 계약 v1을 `1.0.0`으로 적는다.
- `parameters`: `q`, `page`, `limit`, `sort`가 쿼리임을 적는다.
- `gr.Code`: 문서를 실행하지 않고 보여 준다.
- `language="json"`: 색만 JSON에 맞춘다.
- `search_table`: 계약의 목록을 표로 바꾼 같은 함수다.
- `api_name="list_posts"`: Gradio 벨 이름이다. REST 경로 문자열과 같지 않다.

## ④ 🔗 연동 포인트

- 프론트 검색 칸 `q`와 `page`는 이 문서의 쿼리와 같은 이름이다.
- mock 서버의 `/api-docs`와 Gradio의 Use via API를 나란히 열어 어느 쪽이 창고 서류인지 확인한다.
- 오류를 화면에 올릴 때는 `format_error`가 `code`, `message`, `fields`를 문장으로 만든다. 새 오류를 만들면 이 셋과 `requestId`를 유지한다.
- 버전을 올릴 때는 `info.version`과 학습 문서의 표를 먼저 고치고, 그 다음 서비스 테스트를 고친다.

## ⑤ 오류 노트

### 페이지가 0부터 시작

- 증상: 첫 화면이 빈 표다.
- 원인: `page=0`을 보냈다.
- 해결: 화면 기본값은 1이고, 서비스는 1 미만을 400으로 거절한다.

### limit 100이 그대로 적용

- 증상: 한 번에 글 100개를 준다.
- 원인: 상한을 clamp하지 않았다.
- 해결: `list_posts`가 50을 넘으면 50으로 줄인다.

### 정렬 문자열이 SQL에 그대로 들어감

- 증상: 이상한 `sort`에 DB 오류가 난다.
- 원인: 사용자 문자열을 `ORDER BY`에 이었다.
- 해결: `createdAt`, `-createdAt`, `-commentCount`만 허용하고 나머지는 기본 정렬이다.

## ⑥ 직접 해보기

1. study14 화면에서 문서 JSON의 `info.version`을 찾는다.
2. `page`를 1과 2로 바꿔 캡션의 쪽 번호가 바뀌는지 본다.
3. Use via API의 `list_posts`와 문서의 `/api/posts`가 다른 항목임을 한 줄로 적는다.

## ⑦ ☐ 체크리스트

- [ ] 경로는 복수 명사 `/api/posts`다.
- [ ] OpenAPI `info.version`이 계약 버전이다.
- [ ] `page`는 1부터, `limit` 상한은 50이다.
- [ ] 오류 본문에 `code`, `message`, `fields`, `requestId` 자리가 있다.
- [ ] Gradio 자동 API와 REST 문서를 구분했다.
- [ ] 정렬 값은 허용 목록만 통과한다.

## ⑧ 다음 단계

계약이 문서로 남은 상태에서, study15는 같은 목록을 짧게 기억하고 글이 바뀌면 그 기억을 버리며, 걸린 시간을 화면에 적는다.
