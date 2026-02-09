"""Chat: POST /api/chat with session context and streamed reply. Uses web search when context is insufficient."""
import json
import logging
import re
from typing import Generator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agent.constants import LLM_FALLBACK_MESSAGE
from app.config import get_settings
from app.db.session import get_db
from app.models.base import Message, Session as ChatSession
from app.services.web_search import search_web, suggest_search_terms_from_context

logger = logging.getLogger(__name__)
router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: int | None = None


CHAT_MODEL_PRIMARY = "qwen/qwen3-32b"

# Pattern to parse SEARCH_QUERIES: q1 | q2 | q3 from model output
SEARCH_QUERIES_PATTERN = re.compile(r"SEARCH_QUERIES?\s*:\s*(.+?)(?:\n|$)", re.IGNORECASE | re.DOTALL)


def _invoke_chat_llm(prompt: str) -> str:
    """One-shot LLM call. Returns content or empty string."""
    settings = get_settings()
    for api_key, model in [(settings.groq_api_key, CHAT_MODEL_PRIMARY), (settings.groq_api_key_fallback, settings.groq_model_fallback)]:
        if not api_key:
            continue
        try:
            llm = ChatGroq(model=model, api_key=api_key, temperature=0.2)
            out = llm.invoke([HumanMessage(content=prompt)])
            return (out.content or "").strip() if hasattr(out, "content") else str(out).strip()
        except Exception:
            pass
    return ""


def _stream_chat_llm(prompt: str) -> Generator[str, None, None]:
    """Stream chat LLM token-by-token. Yields content chunks. Falls back to full message if stream fails."""
    settings = get_settings()
    primary_key = settings.groq_api_key
    fallback_key = settings.groq_api_key_fallback
    fallback_model = settings.groq_model_fallback
    messages = [HumanMessage(content=prompt)]
    for api_key, model in [(primary_key, CHAT_MODEL_PRIMARY), (fallback_key, fallback_model)]:
        if not api_key:
            continue
        try:
            llm = ChatGroq(model=model, api_key=api_key, temperature=0.3)
            for chunk in llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
            return
        except Exception:
            pass
    for c in (LLM_FALLBACK_MESSAGE or ""):
        yield c


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _parse_search_queries(llm_output: str) -> list[str]:
    """Extract SEARCH_QUERIES: q1 | q2 from model output. Returns empty list if NONE or not found."""
    if not llm_output:
        return []
    m = SEARCH_QUERIES_PATTERN.search(llm_output)
    if not m:
        # Model said NONE or didn't output SEARCH_QUERIES
        return []
    raw = m.group(1).strip()
    if not raw or raw.upper() == "NONE":
        return []
    queries = [q.strip() for q in re.split(r"\||,|;|\n", raw) if q.strip()]
    return queries[:5]


def _chat_stream(session_id: int, message: str, db: Session) -> Generator[str, None, None]:
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not session:
        yield _sse_event("error", {"message": "Session not found"})
        return
    settings = get_settings()
    if settings.dev_mode:
        reply = "Mock reply in Dev mode."
        for c in reply:
            yield _sse_event("message", {"text": c})
    else:
        # Build context from session (always provided to the model)
        summaries = (session.sub_agent_summaries or {}) if hasattr(session, "sub_agent_summaries") else {}
        ctx = (session.scan_context or {}) if hasattr(session, "scan_context") else {}
        symbol = ctx.get("symbol", session.isin)
        history = db.query(Message).filter(Message.session_id == session_id).order_by(Message.created_at).all()
        history_text = "\n".join([f"{m.role}: {m.content[:500]}" for m in history[-10:]])
        analysis_block = f"""Context from prior analysis (always use this):
{json.dumps(summaries, default=str)[:2500]}
Recent conversation:
{history_text}"""

        # Step 1: Decide if we need web search (context insufficient for user question)
        decide_prompt = f"""You are a financial advisor. This session is about stock {symbol}.

{analysis_block}

User now asks: {message}

If the context above does NOT contain enough information to answer the user's question (e.g. reasons for a decline, recent news, commodity drivers), output exactly one line:
SEARCH_QUERIES: query1 | query2 | query3
Use 1-3 search queries: the stock ticker/symbol, related commodity or sector (e.g. "silver price news", "3SIL decline"), or the question topic. If the context is sufficient to answer, output exactly: NONE"""
        decide_out = _invoke_chat_llm(decide_prompt)
        queries = _parse_search_queries(decide_out)
        # When model asked for search, add suggested terms (e.g. commodity from stock name: Silver Lev ETF -> silver)
        if queries:
            suggested = suggest_search_terms_from_context(ctx, symbol or "")
            for s in suggested:
                if s and s not in queries:
                    queries.append(s)
        web_text = ""
        if queries:
            logger.info("chat web_search queries=%s", queries)
            settings = get_settings()
            web_text = search_web(
                queries[:5],
                symbol=symbol or None,
                financial_news_api_key=settings.financial_news_api_key or None,
            )
            web_block = f"\n\nWeb search results (use to supplement the analysis above):\n{web_text[:4000]}"
        else:
            web_block = ""

        # Step 2: Answer using our analysis + optional web results (always include our analysis)
        final_prompt = f"""You are a financial advisor. This session is about stock {symbol}.

{analysis_block}
{web_block}

User now asks: {message}

Answer based on the prior analysis above. If web search results were added, use them to supplement your answer (e.g. reasons for a decline, commodity drivers). Always base your answer on our analysis first; add web-sourced context where it helps. Format your answer in Markdown (use **bold**, ## headers, and lists) for readability."""
        reply = ""
        for chunk in _stream_chat_llm(final_prompt):
            reply += chunk
            yield _sse_event("message", {"text": chunk})
    # Save user message and assistant reply
    db.add(Message(session_id=session_id, role="user", content=message))
    db.add(Message(session_id=session_id, role="assistant", content=reply))
    db.commit()
    yield _sse_event("message", {"text": ""})
    yield _sse_event("done", {"success": True})


@router.post("/chat")
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """Send a message in a session; get streamed reply. Requires session_id from advice flow."""
    if not request.session_id:
        raise HTTPException(status_code=400, detail="session_id required (get it from advice response)")
    return StreamingResponse(
        _chat_stream(request.session_id, request.message, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )
