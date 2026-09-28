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

데이터를 사용할 때는 제공된 수치 밖의 원인을 사실처럼 단정하지 말고, 데이터 기반 해석임을 분명히 하세요.

답변 길이는 질문의 복잡도에 맞추세요. 도움이 된다면 자세한 장문 답변도 충분히 작성해도 됩니다. 다만 읽기 쉽게 핵심부터 말하고, 주제가 바뀔 때는 빈 줄로 문단을 나누며, 여러 추천·단계·비교는 목록으로 한 항목씩 줄바꿈하세요. 긴 내용을 하나의 빽빽한 문단으로 몰아쓰지는 마세요."""


def demo_answer(question, summary):
    return f"현재 데이터는 {summary.period_start}부터 {summary.period_end}까지 {summary.count}건입니다. 평균은 {summary.average}, 범위는 {summary.minimum}~{summary.maximum}이며 {summary.trend_detail} 질문 ‘{question}’에 대해서는 이 요약을 바탕으로 추가 관측을 함께 확인하는 것이 좋습니다. (OPENAI_API_KEY를 설정하면 GPT 답변으로 전환됩니다.)"


def compact_history(messages, max_messages=6, max_chars=7200):
    """Keep recent context useful without overflowing the provider's context window."""
    selected = []
    used = 0
    for message in reversed(messages[-max_messages:]):
        content = str(message.get("content", ""))[:1800]
        if used + len(content) > max_chars:
            continue
        selected.append({"role": message["role"], "content": content})
        used += len(content)
    return list(reversed(selected))


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
        prompt = {"role": "system", "content": system_prompt(summary)}
        request_options = dict(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            # Codyssey's OpenAI-compatible endpoint supports max_tokens
            # (but not GPT-5's reasoning_effort option). A larger allowance
            # leaves room for both reasoning and a visible Korean response.
            max_tokens=2048,
        )
        try:
            response = client.chat.completions.create(
                messages=[prompt, *compact_history(messages), {"role": "user", "content": request.message}],
                **request_options,
            )
            answer = response.choices[0].message.content or "응답 본문이 비어 있습니다."
            mode = "openai"
        except Exception:
            try:
                response = client.chat.completions.create(
                    messages=[prompt, {"role": "user", "content": request.message}],
                    **request_options,
                )
                answer = response.choices[0].message.content or "응답 본문이 비어 있습니다."
                mode = "openai-retry"
            except Exception:
                answer = "AI 응답을 잠시 불러오지 못했습니다. 새 대화를 시작하거나 잠시 후 다시 시도해 주세요."
                mode = "unavailable"
    else:
        answer, mode = demo_answer(request.message, summary), "demo"
    assistant = ChatMessage(role="assistant", content=answer, created_at=datetime.now(timezone.utc)).model_dump(mode="json")
    all_messages = messages + [user, assistant]
    saved = store.save_conversation({"title": (old or {}).get("title", request.message[:36]), "messages": all_messages}, request.conversation_id)
    return {"answer": answer, "conversation_id": saved["id"], "summary": summary, "mode": mode}
