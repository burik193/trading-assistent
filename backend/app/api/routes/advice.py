"""Advice pipeline: POST /api/stocks/{isin}/advice with SSE (progress + main advice stream)."""
import json
import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.agent.sub_agents import (
    run_fundamentals_sub_agent,
    run_main_agent_stream,
    run_math_sub_agent,
    run_news_sub_agent,
    run_price_sub_agent,
)
from app.db.session import get_db
from app.models.base import Message, Session as ChatSession
from app.services.forecast_service import compute_forecast
from app.services.scan_service import ScanService

logger = logging.getLogger(__name__)
router = APIRouter()

TOTAL_STEPS = 10  # resolve, scan steps, price_agent, fundamentals_agent, news_agent, math_agent, main


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _advice_stream(isin: str, db: Session):
    logger.info("advice request start isin=%s", isin)
    progress_list = []

    def on_progress(step_name: str, current: int, total: int, error: Optional[str]):
        progress_list.append({
            "step": step_name,
            "stepIndex": current,
            "totalSteps": total,
            "percent": int(100 * current / total) if total else 0,
            "status": "failed" if error else "ok",
            "message": error,
        })

    scan = ScanService(db)
    ctx = scan.scan(identifier=isin, on_progress=on_progress)
    logger.info("advice scan complete isin=%s symbol=%s", isin, ctx.get("symbol"))
    for p in progress_list:
        yield _sse_event("progress", p)

    symbol = ctx.get("symbol")
    if not symbol:
        logger.warning("advice aborted: symbol not resolved isin=%s", isin)
        yield _sse_event("step_failed", {"step": "Resolving symbol", "message": "Could not resolve ISIN"})
        yield _sse_event("done", {"success": False, "reason": "symbol_not_resolved"})
        return

    step = len(progress_list)
    summaries = {}

    if ctx.get("quote"):
        yield _sse_event("progress", {"step": "Price sub-agent", "stepIndex": step, "totalSteps": TOTAL_STEPS, "percent": int(100 * step / TOTAL_STEPS), "status": "ok", "message": None})
        try:
            s = run_price_sub_agent(ctx["quote"])
            summaries["Price"] = s
        except Exception:
            logger.exception("Price sub-agent failed isin=%s", isin)
            summaries["Price"] = None
            yield _sse_event("step_failed", {"step": "Price sub-agent", "message": "Summary failed"})
        step += 1

    if ctx.get("fundamentals"):
        yield _sse_event("progress", {"step": "Fundamentals sub-agent", "stepIndex": step, "totalSteps": TOTAL_STEPS, "percent": int(100 * step / TOTAL_STEPS), "status": "ok", "message": None})
        try:
            s = run_fundamentals_sub_agent(ctx["fundamentals"])
            summaries["Fundamentals"] = s
        except Exception:
            logger.exception("Fundamentals sub-agent failed isin=%s", isin)
            summaries["Fundamentals"] = None
            yield _sse_event("step_failed", {"step": "Fundamentals sub-agent", "message": "Summary failed"})
        step += 1

    if ctx.get("news"):
        yield _sse_event("progress", {"step": "News sub-agent", "stepIndex": step, "totalSteps": TOTAL_STEPS, "percent": int(100 * step / TOTAL_STEPS), "status": "ok", "message": None})
        try:
            s = run_news_sub_agent(ctx["news"])
            summaries["News"] = s
        except Exception:
            logger.exception("News sub-agent failed isin=%s", isin)
            summaries["News"] = None
            yield _sse_event("step_failed", {"step": "News sub-agent", "message": "Summary failed"})
        step += 1

    yield _sse_event("progress", {"step": "Math/analysis sub-agent", "stepIndex": step, "totalSteps": TOTAL_STEPS, "percent": int(100 * step / TOTAL_STEPS), "status": "ok", "message": None})
    daily_series = ctx.get("daily") or []
    # Use up to 1 year (252 trading days) for mathematical analysis and forecast
    daily_sample = daily_series[-252:] if len(daily_series) > 252 else daily_series
    forecast_data = compute_forecast(daily_series) if len(daily_series) >= 2 else {}
    math_ctx = {
        "quote": ctx.get("quote"),
        "daily_sample": daily_sample,
        "fundamentals": ctx.get("fundamentals"),
        "forecast": forecast_data,
    }
    try:
        math_s = run_math_sub_agent(math_ctx)
        summaries["Math/Analysis"] = math_s
    except Exception:
        logger.exception("Math sub-agent failed isin=%s", isin)
        summaries["Math/Analysis"] = None
        yield _sse_event("step_failed", {"step": "Math/analysis sub-agent", "message": "Summary failed"})
    step += 1

    # Add near-term forecast to context so main agent can use it in advice
    if forecast_data.get("forecast") and forecast_data.get("stats"):
        stats = forecast_data["stats"]
        forecast_summary_parts = [
            f"Next 3 trading days (linear trend extrapolation): " + ", ".join(
                f"{p['time']}={p['close']:.2f}" for p in forecast_data["forecast"]
            ),
            f"Trend slope: {stats.get('slope', 0):.4f}, std: {stats.get('std', 0):.2f}.",
        ]
        summaries["Forecast"] = " ".join(forecast_summary_parts)
        logger.info("advice forecast added to context isin=%s", isin)

    yield _sse_event("progress", {"step": "Main synthesis", "stepIndex": step, "totalSteps": TOTAL_STEPS, "percent": 95, "status": "ok", "message": None})
    advice_text = ""
    try:
        for chunk in run_main_agent_stream(summaries, symbol):
            advice_text += chunk
            yield _sse_event("advice_chunk", {"text": chunk})
    except Exception:
        logger.exception("Main agent failed isin=%s symbol=%s", isin, symbol)
        yield _sse_event("step_failed", {"step": "Main synthesis", "message": "LLM synthesis failed"})
        yield _sse_event("done", {"success": False, "reason": "main_agent_error"})
        return

    if not advice_text:
        logger.warning("Main agent returned empty isin=%s symbol=%s", isin, symbol)
        advice_text = "Unable to generate advice (LLM or summaries failed)."
        yield _sse_event("done", {"success": False, "reason": "main_agent_empty"})
        return

    # Create session and store advice as assistant message
    chat_session = ChatSession(
        isin=isin,
        title=f"{symbol or isin} – {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
        scan_context=ctx,
        sub_agent_summaries=summaries,
    )
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    msg = Message(session_id=chat_session.id, role="assistant", content=advice_text)
    db.add(msg)
    db.commit()

    logger.info("advice success isin=%s session_id=%s", isin, chat_session.id)
    yield _sse_event("advice_chunk", {"text": ""})
    yield _sse_event("done", {"success": True, "sessionId": chat_session.id})


@router.post("/stocks/{isin}/advice")
async def get_advice(isin: str, request: Request, db: Session = Depends(get_db)):
    """Run advice pipeline: scan + sub-agents + main agent. Stream progress and advice via SSE."""
    return StreamingResponse(
        _advice_stream(isin, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
