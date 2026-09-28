import os
from datetime import datetime, timezone

from fastapi import APIRouter
from openai import OpenAI

from ..schemas import ChatMessage, ChatRequest
from ..services.store import store
from ..services.summary import make_summary

router = APIRouter(prefix="/api/chat", tags=["chat"])


def system_prompt(summary):
    return f"""당신은 친절한 한국어 게임 챗봇 "Game Pulse AI"입니다.
사용자의 질문에 자연스럽고 직접적으로 답하세요. 게임 추천, 장르, 공략, 개발, 잡담을 포함한 일반적인 질문도 평소 챗봇처럼 대화하세요. 질문이 시계열 데이터·게임 관심도·추세·통계·데이터에 근거한 추천과 명확하게 관련된 경우에만 아래 요약을 활용하세요. 관련 없는 질문에는 데이터 요약이나 관측치를 불필요하게 언급하지 마세요.

데이터 요약(관련 질문에만 사용): 기간 {summary.period_start} ~ {summary.period_end}; 관측치 {summary.count}개; 평균 {summary.average}; 최소/최대 {summary.minimum}/{summary.maximum}; 추세 {summary.trend}; 설명 {summary.trend_detail}

데이터를 사용할 때는 제공된 수치 밖의 원인을 사실처럼 단정하지 말고, 데이터 기반 해석임을 분명히 하세요."""


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
