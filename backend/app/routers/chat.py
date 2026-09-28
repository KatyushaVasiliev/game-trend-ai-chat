import os
from datetime import datetime, timezone

from fastapi import APIRouter
from openai import OpenAI

from ..schemas import ChatMessage, ChatRequest
from ..services.store import store
from ..services.summary import make_summary

router = APIRouter(prefix="/api/chat", tags=["chat"])


def system_prompt(summary):
    return f"""당신은 게임 시계열 데이터 분석 어시스턴트입니다. 아래의 검증된 데이터 요약만 근거로 한국어로 답하세요.
기간: {summary.period_start} ~ {summary.period_end}; 관측치: {summary.count}개; 평균: {summary.average}; 최소/최대: {summary.minimum}/{summary.maximum}; 추세: {summary.trend}; 설명: {summary.trend_detail}
수치가 없는 원인을 단정하지 말고, 질문과 데이터의 관계를 명확하게 설명하세요."""


def demo_answer(question, summary):
    return f"현재 데이터는 {summary.period_start}부터 {summary.period_end}까지 {summary.count}건입니다. 평균은 {summary.average}, 범위는 {summary.minimum}~{summary.maximum}이며 {summary.trend_detail} 질문 ‘{question}’에 대해서는 이 요약을 바탕으로 추가 관측을 함께 확인하는 것이 좋습니다. (OPENAI_API_KEY를 설정하면 GPT 답변으로 전환됩니다.)"


@router.post("")
def chat(request: ChatRequest):
    summary = make_summary(store.list_data())
    old = store.get_conversation(request.conversation_id) if request.conversation_id else None
    messages = (old or {}).get("messages", [])
    user = ChatMessage(role="user", content=request.message, created_at=datetime.now(timezone.utc)).model_dump(mode="json")
    if os.getenv("OPENAI_API_KEY"):
        client_options = {"api_key": os.environ["OPENAI_API_KEY"]}
        base_url = os.getenv("OPENAI_BASE_URL", "").strip()
        if base_url:
            client_options["base_url"] = base_url
        client = OpenAI(**client_options)
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": system_prompt(summary)},
                *[{"role": m["role"], "content": m["content"]} for m in messages[-12:] + [user]],
            ],
            # Codyssey's OpenAI-compatible endpoint supports max_tokens
            # (but not GPT-5's reasoning_effort option). A larger allowance
            # leaves room for both reasoning and a visible Korean response.
            max_tokens=2048,
        )
        answer = response.choices[0].message.content or "응답 본문이 비어 있습니다."
        mode = "openai"
    else:
        answer, mode = demo_answer(request.message, summary), "demo"
    assistant = ChatMessage(role="assistant", content=answer, created_at=datetime.now(timezone.utc)).model_dump(mode="json")
    all_messages = messages + [user, assistant]
    saved = store.save_conversation({"title": (old or {}).get("title", request.message[:36]), "messages": all_messages}, request.conversation_id)
    return {"answer": answer, "conversation_id": saved["id"], "summary": summary, "mode": mode}
