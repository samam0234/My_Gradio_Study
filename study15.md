# study15. 성능·캐시

## ① 목표

같은 목록 조회를 짧게 기억하고, 글이 바뀌면 기억을 버리며, 비동기 함수와 걸린 시간을 화면에서 확인한다.

## ② 📖 이론

### 왜 쓰는지

검색 버튼을 연속으로 누르면 같은 SQL이 반복된다. 결과를 무조건 오래 기억하면 방금 쓴 글이 표에 없다. 기억의 키와 버리는 시점을 정해야 한다. 시간이 걸리는 일은 이벤트 함수를 비동기로 둘 수 있고, Gradio 큐가 그 호출을 줄 세운다.

### 핵심 개념

- **ListCache**: 키 `(q, page, limit, sort)`와 세대 번호. 조회 전에 `invalidate()`하면 세대가 올라가 이전 값이 무효가 된다.
- **측정**: `time.perf_counter`로 밀리초를 재어 캡션에 `hit` 또는 `miss`를 붙인다.
- **비동기**: `async def` 안에서 `await asyncio.sleep(0)` 뒤에 결과를 돌려준다. Gradio는 이 코루틴을 이벤트로 받을 수 있다.
- **큐**: `click(..., queue=True)`가 기본에 가깝다. study5의 `concurrency_limit`과 함께 동시 실행 수를 제한한다.
- **백그라운드**: 이 학습에서 오래 걸리는 파일 작업은 요청 안에서 끝내고 결과 문장만 돌려준다. 프로세스 밖에 워커를 두지 않는다.

### 비유

캐시는 방금 찾아 둔 색인 카드다. 서가에 책을 새로 꽂으면 카드 더미 전체에 "이전 판" 도장을 찍어 다시 찾게 한다. 시간을 재는 것은 손님이 기다린 초를 영수증에 적는 일이다.

## ③ 🛠️ 실기

`board/cache.py`

```python
class ListCache:
    def __init__(self) -> None:
        self.generation = 0
        self._items: dict = {}

    def get(self, key: tuple):
        found = self._items.get(key)
        if found is None or found[0] != self.generation:
            return None
        return found[1]

    def put(self, key: tuple, value) -> None:
        self._items[key] = (self.generation, value)

    def invalidate(self) -> None:
        self.generation += 1
```

`cached_list`는 같은 키가 유효하면 저장 값을 돌려주고 `hit=True`다. 없으면 `search_table`을 호출한 뒤 저장한다.

`apps/perf_demo.py`는 검색 버튼으로 `measured`를 부르고, "캐시 비우기"로 `invalidate`를 부른다. "비동기 따라 하기"는 `slow_echo`를 연결한다.

```python
async def slow_echo(text: str) -> str:
    await asyncio.sleep(0)
    return (text or "").strip() or "비어 있음"
```

```powershell
gradio demo/study15/app.py
```

같은 검색어로 두 번 누르면 둘째 캡션에 `cache=hit`가 보여야 한다. 비우기 다음에는 `miss`다.

### 줄별 설명

- `generation`: 기억을 지울 때 딕셔너리를 비우지 않아도 이전 세대 값이 `get`에서 탈락한다.
- `key`: 검색어와 쪽이 같아야 같은 결과다. 토큰은 키에 넣지 않는다. 공개 목록만 기억한다.
- `perf_counter`: 벽시계보다 짧은 구간을 재는 데 맞다.
- `hit`: 저장소 호출을 건너뛰었다는 표시다.
- `async def`: 이벤트 함수가 코루틴이다.
- `asyncio.sleep(0)`: 이벤트 루프에 한 번 양보한다. 학습용으로 0초다.
- `invalidate`: 글을 만든 뒤 목록 함수가 이 메서드를 불러야 새 글이 보인다. 성능 화면은 버튼으로 그 동작을 보여 준다.

## ④ 🔗 연동 포인트

- 공개 목록만 캐시한다. 로그인 사용자만 보는 초안은 `State`에 둔다.
- 작성·수정·삭제가 성공하면 `invalidate`를 호출해야 study6의 표가 새 글을 받는다. 캐시 키에 토큰을 넣지 않는 이유와 같다.
- 측정 문장은 화면에만 남기고, 운영 로그에는 경로와 밀리초만 남긴다. study16이 그 로그를 본다.
- 비동기 함수도 같은 `inputs`/`outputs` 계약이다. 화면 쪽 코드가 코루틴을 직접 `await`하지 않는다.

## ⑤ 오류 노트

### 새 글이 표에 없음

- 증상: 작성 직후 검색이 이전 목록이다.
- 원인: 세대 번호를 올리지 않았다.
- 해결: 성공한 쓰기 뒤에 `invalidate`를 호출한다.

### 캐시 키에 토큰이 있음

- 증상: 사용자마다 같은 공개 목록을 다시 읽는다. 또는 키가 로그에 남는다.
- 원인: 토큰 문자열을 키에 넣었다.
- 해결: 키는 `q`, `page`, `limit`, `sort`만이다.

### hit인데 매우 느림

- 증상: 캡션은 hit인데 밀리초가 크다.
- 원인: 측정 구간에 화면 전송까지 포함됐거나 다른 블로킹이 있다.
- 해결: `cached_list` 안의 숫자만 비교한다. 첫 miss와 둘째 hit의 차이로 본다.

## ⑥ 직접 해보기

1. 같은 검색을 두 번 눌러 `miss` 다음 `hit`을 확인한다.
2. 비우기 후 다시 검색해 `miss`로 돌아오는지 본다.
3. 비동기 버튼에 문장을 넣어 같은 문장이 결과 칸에 돌아오는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 목록 캐시의 키에 토큰이 없다.
- [ ] `invalidate` 후 다음 조회는 miss다.
- [ ] 캡션에 밀리초와 hit/miss가 있다.
- [ ] 비동기 이벤트 함수가 `async def`다.
- [ ] 공개 목록과 사용자 상태를 한 캐시에 넣지 않는다.

## ⑧ 다음 단계

걸린 시간을 볼 수 있는 상태에서, study16은 테스트 자동 실행, 컨테이너, 로그, 백업을 배포 전에 확인하는 목록으로 모은다.
