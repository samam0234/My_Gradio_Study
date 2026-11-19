# study17. 실시간·확장

## ① 목표

알림 파일을 주기적으로 다시 읽어 화면에 올리고, 텍스트 파일의 줄과 글자 수를 같은 앱에서 처리한다.

## ② 📖 이론

### 왜 쓰는지

게시판은 버튼을 누를 때만 갱신된다. 다른 작업이 남긴 알림을 보려면 페이지를 새로고침하거나, 일정 간격으로 파일을 다시 읽어야 한다. Gradio의 `gr.Timer`는 그 간격마다 함수를 부른다. 브라우저와 서버가 이미 연결을 유지하므로 별도의 소켓 서버를 앱 옆에 두지 않아도 된다.

### 핵심 개념

- **gr.Timer**: `gr.Timer(5)`는 5초마다 `tick` 이벤트를 만든다.
- **알림 파일**: `data/notice.txt`. 버튼이 한 줄을 쓰고, 타이머가 그 파일을 읽어 칸에 넣는다.
- **파일 처리**: `.txt`와 `.md`만 읽어 줄 수와 글자 수를 센다. 실행 파일은 열지 않는다.
- **확장**: 새 기능은 탭이나 이벤트 하나로 붙인다. 게시판 `service`의 상태 코드를 바꾸지 않는다.

### 비유

타이머는 매장 시계다. 시계가 울릴 때마다 점원이 게시판 서랍이 아니라 알림 메모지를 다시 읽는다. 메모지가 비어 있으면 "새 알림 없음"이라고만 말한다.

## ③ 🛠️ 실기

`board/notify.py`

```python
def read_notice(path: Path) -> str:
    if not path.exists():
        return "새 알림 없음"
    text = path.read_text(encoding="utf-8").strip()
    return text or "새 알림 없음"


def write_notice(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip(), encoding="utf-8")
```

`apps/realtime_demo.py`

```python
timer = gr.Timer(5)
timer.tick(lambda: read_notice(notice), outputs=live)
gr.Button("줄 수 세기").click(summarize_file, inputs=upload, outputs=summary, api_name="summarize_file")
```

`summarize_file`은 경로가 없거나 확장자가 txt, md가 아니면 `gr.Error`를 올린다. 내용이 있으면 `N줄, M자`를 돌려준다.

```powershell
gradio demo/study17/app.py
```

알림을 남긴 뒤 5초 안에 칸이 그 문장으로 바뀌는지 본다. 페이지를 새로고침하지 않는다.

### 줄별 설명

- `read_notice`: 파일이 없거나 공백만 있으면 같은 안내 문장이다.
- `write_notice`: 디렉터리를 만들고 한 파일만 덮어쓴다. 알림 이력 전체가 아니다.
- `gr.Timer(5)`: 초 단위 간격이다. 너무 짧으면 파일 읽기가 잦아진다.
- `timer.tick`: 클릭과 같은 이벤트다. 입력이 없고 출력 칸만 있다.
- `summarize_file`: 업로드 경로를 읽어 센다. 파일을 실행하지 않는다.
- `encoding="utf-8"`: 한글 줄이 깨지지 않게 한다. 깨진 바이트는 `errors="replace"`로 글자 수 계산만 계속한다.
- `api_name="summarize_file"`: 화면 없이 같은 세기를 부를 때의 이름이다.

## ④ 🔗 연동 포인트

- 알림 파일은 `data/`라 Git에 없다. 다른 프로세스가 같은 경로에 한 줄을 써도 타이머가 읽는다.
- 게시판 새 글을 알림으로 올리려면 작성 성공 뒤에 `write_notice`를 호출한다. 목록 캐시를 쓰는 경우에는 study15의 `invalidate`도 같이 호출한다.
- 파일 줄 수 결과는 게시판 본문에 자동으로 들어가지 않는다. 필요할 때만 작성 칸에 사람이 복사한다.
- study18의 스트리밍은 타이머와 다르다. 스트리밍은 한 번의 질문 응답을 잘게 나누고, 타이머는 바깥 파일을 반복해서 읽는다.

## ⑤ 오류 노트

### 알림이 안 바뀜

- 증상: 버튼을 눌러도 칸이 그대로다.
- 원인: 타이머가 아직 한 번도 울리지 않았거나, 쓰는 경로와 읽는 경로가 다르다.
- 해결: 5초를 기다린다. 둘 다 `data/notice.txt`인지 확인한다.

### 타이머가 너무 잦음

- 증상: 터미널 로그가 읽기 호출로 가득 찬다.
- 원인: 간격을 1초 미만으로 줄였다.
- 해결: 학습 기본값 5초를 유지한다.

### md가 거절됨

- 증상: 확장자 오류.
- 원인: 대문자 `.TXT`만 허용했다.
- 해결: 비교 전에 `suffix.lower()`를 쓴다.

## ⑥ 직접 해보기

1. 알림 문장을 저장하고 새로고침 없이 칸이 바뀌는지 시간을 재 본다.
2. txt 파일을 올려 줄 수가 에디터의 줄 수와 같은지 비교한다.
3. png를 줄 수 버튼에 넣어 오류 창이 나는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `gr.Timer`가 알림 파일을 주기적으로 읽는다.
- [ ] 알림이 없을 때의 문장이 정해져 있다.
- [ ] txt와 md만 줄 수를 센다.
- [ ] 파일을 실행하지 않는다.
- [ ] 이 확장이 게시판 상태 코드를 바꾸지 않는다.

## ⑧ 다음 단계

주기적으로 파일을 읽는 확장이 붙은 상태에서, study18은 문서 발췌로 답하는 챗, 스트리밍, 리뷰 표시, MCP 도구를 한 화면에 모은다.
