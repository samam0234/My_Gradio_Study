"""문서 발췌 답변과 규칙 기반 리뷰 표시.

외부 모델이 있으면 그 응답을 쓰고, 없으면 이 파일의 함수로 화면을 확인한다.
모델 가중치나 카드 번호를 여기에 두지 않는다.
"""

from __future__ import annotations

import requests

SUSPICIOUS = ("클릭", "공짜", "무료 돈", "대박", "100%", "http://", "https://")


def chunks(text: str) -> list[str]:
    parts = [part.strip() for part in (text or "").split("\n\n") if part.strip()]
    if parts:
        return parts
    stripped = (text or "").strip()
    return [stripped] if stripped else []


def ask_document(document: str, question: str) -> str:
    query = (question or "").strip()
    if not query:
        return "질문을 입력해 주세요."
    pieces = chunks(document)
    if not pieces:
        return "문서에서 찾을 수 없습니다."
    terms = [term for term in query.casefold().split() if term]
    scored: list[tuple[int, int, str]] = []
    for index, piece in enumerate(pieces, start=1):
        haystack = piece.casefold()
        score = sum(haystack.count(term) for term in terms)
        if score:
            scored.append((score, index, piece))
    if not scored:
        return "문서에서 찾을 수 없습니다."
    scored.sort(key=lambda item: (-item[0], item[1]))
    lines = ["문서에서 찾은 내용만 적습니다.", ""]
    for _score, index, piece in scored[:3]:
        lines.append(f"(발췌 {index}) {piece}")
    return "\n".join(lines)


def build_prompt(document: str, question: str) -> str:
    return (
        "다음 문서에 있는 문장만 근거로 답한다. "
        "근거가 없으면 문서에서 찾을 수 없습니다 라고만 답한다.\n"
        f"문서:\n{document}\n\n질문:\n{question}"
    )


def call_model(url: str, api_key: str, prompt: str, timeout: float = 20.0) -> str:
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    response = requests.post(url, json={"prompt": prompt}, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        for key in ("answer", "text", "output"):
            if payload.get(key):
                return str(payload[key])
    return response.text


def answer(document: str, question: str, model_url: str = "", model_key: str = "") -> str:
    if model_url:
        try:
            return call_model(model_url, model_key, build_prompt(document, question))
        except requests.RequestException:
            local = ask_document(document, question)
            return "모델 API에 연결하지 못해 발췌 검색으로 답합니다.\n" + local
    return ask_document(document, question)


def stream_text(text: str):
    built = ""
    for char in text:
        built += char
        yield built


def highlight(text: str) -> list[tuple[str, str | None]]:
    pieces: list[tuple[str, str | None]] = []
    rest = text
    while rest:
        hit_at = None
        hit_word = ""
        for word in SUSPICIOUS:
            found = rest.find(word)
            if found >= 0 and (hit_at is None or found < hit_at):
                hit_at = found
                hit_word = word
        if hit_at is None:
            pieces.append((rest, None))
            break
        if hit_at:
            pieces.append((rest[:hit_at], None))
        pieces.append((hit_word, "suspicious"))
        rest = rest[hit_at + len(hit_word) :]
    return pieces


def analyze_review(text: str, image_path: str | None = None) -> dict:
    raw = (text or "").strip()
    if not raw:
        raise ValueError("리뷰 텍스트를 입력하세요.")
    hits = [word for word in SUSPICIOUS if word in raw]
    probability = min(1.0, len(hits) / 3 + (0.05 if image_path else 0.0))
    if probability < 0.4:
        label = "Genuine"
    elif probability < 0.7:
        label = "Suspicious"
    else:
        label = "Fake"
    return {
        "summary": f"판정: {label}",
        "probabilities": {"Fake": round(probability, 4), "Genuine": round(1 - probability, 4)},
        "highlights": highlight(raw),
        "raw": {
            "label": label,
            "probability": round(probability, 4),
            "imageUsed": bool(image_path),
            "engine": "local-rules",
        },
    }
