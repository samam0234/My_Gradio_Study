# study18. AI 연동·MCP

## ① 목표

문서 안의 문장만 근거로 답하는 챗을 스트리밍으로 보여주고, 리뷰 문장을 표시하며, 같은 함수를 MCP 도구로 부르는 연습을 한다.

## ② 📖 이론

### 왜 쓰는지

Gradio는 모델 데모 화면에 자주 붙는다. 모델 키가 없어도 화면의 흐름(입력, 스트리밍, 하이라이트, 도구 호출)은 연습할 수 있다. 키가 있으면 같은 함수가 HTTP로 프롬프트를 보내고, 실패하면 발췌 검색으로 돌아온다.

노션의 [DocuForge](https://app.notion.com/p/40bd7dec5e2e818d9c91c6fb26dccc4c)는 문서를 올리면 요약하고, 문서 밖 내용은 "찾을 수 없습니다"로 답한다. 이 단원은 그 규칙만 Gradio 챗으로 축소한 것이다. 화면이 문서 텍스트를 직접 받고, 발췌 번호 `(발췌 N)`을 답에 붙인다.

노션의 [ReviewForge](https://app.notion.com/p/40bd7dec5e2e81f5af33fa01a3b473c1)는 `ai-server/gradio_app.py`가 같은 추론기를 브라우저에서 바로 시험한다. 그 호출은 기록에 남지 않는다. 이 저장소의 리뷰 탭은 그 화면 배치를 따르고, 점수는 로컬 규칙이다. `model_service.analyze`의 가중치를 가져오지 않는다.

### 핵심 개념

- **프롬프트**: 문서에 있는 문장만 근거로 답하고, 없으면 "문서에서 찾을 수 없습니다"라고 말하라는 지시와 문서, 질문을 한 문자열로 붙인다.
- **발췌**: 빈 줄로 나눈 문단. 질문 단어가 들어 있는 문단만 고른다. 하나도 없으면 찾을 수 없다는 문장만 돌려준다.
- **gr.ChatInterface**: `fn(message, history, document)`가 도우미 문장을 yield하면 스트리밍이다.
- **스트리밍**: `stream_text`가 한 글자씩 누적 문자열을 yield한다.
- **리뷰 표시**: `gr.HighlightedText`는 `(조각, 라벨 또는 None)` 목록이다. 의심 단어만 `suspicious`다. `gr.Label`은 `{"Fake": p, "Genuine": 1-p}`다.
- **MCP**: `launch(mcp_server=True)`는 `api_name`이 있는 이벤트를 도구로 연다. `board/mcp_tools.py`의 `call_tool`은 그 도구를 프로세스 안에서 불러 보는 클라이언트 연습이다.
- **모델 API**: `MODEL_API_URL`에 `{"prompt": ...}`를 POST한다. `MODEL_API_KEY`는 `Authorization: Bearer`로만 보내고 로그에 남기지 않는다.

### 비유

챗은 문서 더미 앞에서 답하는 창구다. 더미에 없는 내용은 "그 페이지가 없습니다"라고만 말한다. MCP는 그 창구 벨에 바깥 이름표를 붙이는 일이다.

## ③ 🛠️ 실기

`board/ai.py`의 `ask_document`와 `build_prompt`, `analyze_review`가 규칙이다. 화면은 `apps/ai_demo.py`다.

챗:

```python
def chat(message, history, document):
    del history
    text = answer(document or "", message or "", settings["model_api_url"], settings["model_api_key"])
    yield from stream_text(text)

document = gr.Textbox(label="문서", lines=8)
gr.ChatInterface(fn=chat, additional_inputs=[document], title="발췌 챗", api_name="ask_document")
```

리뷰 탭은 왼쪽 입력, 오른쪽 출력이다.

```python
text_in = gr.Textbox(label="리뷰 텍스트", lines=6)
image_in = gr.Image(label="리뷰 사진 (선택)", type="filepath", sources=["upload"])
button = gr.Button("분석", variant="primary")
button.click(
    review,
    inputs=[text_in, image_in],
    outputs=[summary_out, prob_out, highlight_out, json_out],
    api_name="analyze_review",
)
```

빈 리뷰는 `raise gr.Error("리뷰 텍스트를 입력하세요.")`다. 예문 둘은 `gr.Examples`가 텍스트 칸에 넣는다.

MCP 연습:

```python
TOOLS = (
    {"name": "search_posts", "description": "게시글 제목을 검색해 id와 title 표를 돌려준다."},
    {"name": "ask_document", "description": "문서 발췌 안에서만 질문에 답한다."},
)
```

`call_tool(gateway, name, arguments)`가 이름에 따라 `search_table` 또는 `ask_document`를 부른다. 모르는 이름은 `error` 키를 돌려준다. 외부 MCP 클라이언트를 붙일 때만 `.env`의 `GRADIO_MCP=true`로 `launch(mcp_server=True)`를 켠다.

```powershell
gradio demo/study18/app.py
```

문서 기본값에는 "Gradio는 함수를 화면에 연결합니다."가 있다. 질문 "Gradio 함수"에는 발췌 번호가 있어야 하고, 질문 "주식 시세"에는 찾을 수 없다는 문장이 있어야 한다.

### 줄별 설명

- `del history`: 이번 답은 이전 대화를 근거로 쓰지 않는다. 근거는 문서 칸뿐이다.
- `answer`: URL이 없으면 `ask_document`, 있으면 모델을 호출하고 연결 실패 시 발췌로 돌아온다.
- `yield from stream_text`: 누적 문자열을 여러 번 돌려 챗이 길어 보이게 한다.
- `additional_inputs`: 챗 입력 외에 문서 칸을 함수의 세 번째 인자로 넣는다.
- `gr.ChatInterface`: 메시지 목록 UI다. `fn`의 첫 인자는 이번 사용자 문장이다.
- `analyze_review`: 의심 단어 비율로 0~1 점수를 만든다. `engine`은 `local-rules`다.
- `HighlightedText`: 튜플 목록. `None` 라벨은 보통 문장이다.
- `gr.Label`: 두 클래스의 확률 딕셔너리다.
- `gr.Examples`: 예문 클릭이 입력 칸을 채운다.
- `call_tool`: 테스트가 브라우저 없이 도구 결과를 확인하는 입구다.

## ④ 🔗 연동 포인트

- DocuForge의 흐름(문서 → 발췌 → 근거 있는 답 또는 없음)을 이 챗이 한 프로세스에서 재현한다. Vue나 Rails 코드를 이 저장소에 붙이지 않는다. 실제 프로젝트는 프론트가 API만 부르고, AI 서버가 발췌를 고른다.
- ReviewForge는 Gradio 7860이 Flask 추론을 직접 시험하고 저장하지 않는다. 이 탭의 JSON에도 사용자 계정이 없다. 기록을 남기려면 게시판 API를 따로 호출해야 한다.
- `MODEL_API_URL`이 비어 있으면 네트워크를 열지 않는다. 키는 `.env`에만 둔다.
- `GRADIO_MCP=true`일 때 이벤트의 `api_name`이 도구 이름과 만난다. `search_posts`는 study6의 검색과 같은 함수다.
- 스트리밍이 끝난 최종 문자열만 로그에 남긴다. 프롬프트 원문에 키가 들어가지 않게 `build_prompt`는 문서와 질문만 붙인다.

## ⑤ 오류 노트

### 문서 밖 내용을 지어 답함

- 증상: 발췌에 없는 설명이 답에 있다.
- 원인: 모델 URL이 켜져 있고 그 모델이 지시를 무시했다. 또는 발췌가 없을 때도 일반 문장을 붙였다.
- 해결: 로컬 `ask_document`는 점수가 0이면 찾을 수 없다는 문장만 돌려준다. 모델을 쓸 때도 `build_prompt`의 지시를 유지하고, 결과를 발췌와 비교한다.

### 빈 리뷰가 확률을 만듦

- 증상: 공백 입력에 Genuine이 나온다.
- 원인: `strip` 전에 점수를 계산했다.
- 해결: 빈 문자열은 `gr.Error`다.

### MCP 클라이언트가 도구를 못 봄

- 증상: 외부 클라이언트가 연결되지 않는다.
- 원인: `GRADIO_MCP`가 꺼져 있다.
- 해결: 필요할 때만 true로 켜고, 연습은 화면의 `call_tool`과 pytest로 확인한다.

## ⑥ 직접 해보기

1. 기본 문서에 "Gradio 함수"와 "주식 시세"를 각각 물어 발췌 답과 없음 답을 비교한다.
2. 리뷰 예문 둘을 눌러 확률과 하이라이트가 달라지는지 본다. 빈 문장은 오류여야 한다.
3. MCP 탭에서 `ask_document`를 호출해 챗과 같은 없음 문장이 JSON에 있는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `gr.ChatInterface` 로 챗 화면 (LLM API 연동 연습)
- [ ] 근거가 없으면 "문서에서 찾을 수 없습니다"만 답한다.
- [ ] 답변을 `yield`로 스트리밍한다.
- [ ] 리뷰 하이라이트가 `(조각, 라벨 또는 None)` 목록이다.
- [ ] 빈 리뷰는 `gr.Error`다.
- [ ] 모델 키를 로그와 문서에 남기지 않는다.
- [ ] `call_tool`로 `search_posts`와 `ask_document`를 구분한다.
- [ ] DocuForge의 발췌 규칙과 ReviewForge의 Blocks 배치를 이 화면에서 가리킬 수 있다.

## ⑧ 다음 단계

챗과 리뷰 표시와 도구 호출이 한 화면에 있으면, `studyFinal.md`에서 midpoint 게시판과 이 심화 기능을 한 서비스로 묶고 배포 전에 점검한다.
