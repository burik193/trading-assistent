"""Sub-agents: per-step and math/analysis. Summarize context into short advice snippets."""
import logging
from typing import Any, Generator, List, Optional

from langchain_core.messages import BaseMessage, HumanMessage
from langchain_groq import ChatGroq

from app.agent.constants import LLM_FALLBACK_MESSAGE
from app.config import get_settings

logger = logging.getLogger(__name__)

GROQ_MODEL = "qwen/qwen3-32b"
_llm_key_warned = False


def _invoke_llm(messages: List[BaseMessage]) -> Optional[str]:
    """Try primary GROQ; on exception try fallback key/model. Return content or None."""
    settings = get_settings()
    primary_key = settings.groq_api_key
    fallback_key = settings.groq_api_key_fallback
    fallback_model = settings.groq_model_fallback
    global _llm_key_warned
    if not primary_key and not fallback_key:
        if not _llm_key_warned:
            _llm_key_warned = True
            logger.warning("No GROQ API key set; LLM calls will return fallback")
        return None
    # Primary
    if primary_key:
        try:
            llm = ChatGroq(model=GROQ_MODEL, api_key=primary_key, temperature=0.3)
            out = llm.invoke(messages)
            return out.content if hasattr(out, "content") else str(out)
        except Exception as e:
            logger.debug("Primary LLM invoke failed: %s", e)
    # Fallback
    if fallback_key:
        try:
            llm = ChatGroq(model=fallback_model, api_key=fallback_key, temperature=0.3)
            out = llm.invoke(messages)
            return out.content if hasattr(out, "content") else str(out)
        except Exception as e:
            logger.debug("Fallback LLM invoke failed: %s", e)
    return None


def _stream_llm(messages: List[BaseMessage]) -> Generator[str, None, None]:
    """Stream LLM response token-by-token. Yields content chunks. Empty if no key or all fail."""
    settings = get_settings()
    primary_key = settings.groq_api_key
    fallback_key = settings.groq_api_key_fallback
    fallback_model = settings.groq_model_fallback
    global _llm_key_warned
    if not primary_key and not fallback_key:
        if not _llm_key_warned:
            _llm_key_warned = True
            logger.warning("No GROQ API key set; LLM stream will yield nothing")
        return
    for api_key, model in [(primary_key, GROQ_MODEL), (fallback_key, fallback_model)]:
        if not api_key:
            continue
        try:
            llm = ChatGroq(model=model, api_key=api_key, temperature=0.3)
            for chunk in llm.stream(messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
            return
        except Exception as e:
            logger.debug("LLM stream failed with %s: %s", model, e)
    return


def run_price_sub_agent(context: dict[str, Any]) -> Optional[str]:
    """Summarize price/quote context: how stock behaves, what numbers suggest."""
    if get_settings().dev_mode:
        return "Mock summary for price (Dev mode)."
    prompt = f"""You are a financial analysis sub-agent. Summarize the following price/quote data for the stock in 2-4 short sentences. Focus on: current price, volume, change; how the stock is behaving; what the numbers suggest. No buy/sell recommendation yet.

Data:
{context}
"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    return result if result is not None else LLM_FALLBACK_MESSAGE


def run_fundamentals_sub_agent(context: dict[str, Any]) -> Optional[str]:
    """Summarize fundamentals: ratios, health, what analysis suggests."""
    if get_settings().dev_mode:
        return "Mock summary for fundamentals (Dev mode)."
    prompt = f"""You are a financial analysis sub-agent. Summarize the following fundamental data in 2-4 short sentences. Focus on: key ratios (P/E, etc.), financial health; what the analysis suggests. No buy/sell recommendation yet.

Data:
{context}
"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    return result if result is not None else LLM_FALLBACK_MESSAGE


def run_news_sub_agent(context: list[dict[str, Any]]) -> Optional[str]:
    """Summarize news/sentiment: sentiment, key themes."""
    if get_settings().dev_mode:
        return "Mock summary for news (Dev mode)."
    prompt = f"""You are a financial analysis sub-agent. Summarize the following news/sentiment in 2-4 short sentences. Focus on: overall sentiment, key themes, recent events. No buy/sell recommendation yet.

Data:
{context}
"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    return result if result is not None else LLM_FALLBACK_MESSAGE


def run_math_sub_agent(context: dict[str, Any]) -> Optional[str]:
    """Summarize mathematical/analytical context only: series summary, metrics, stats, and near-term forecast."""
    if get_settings().dev_mode:
        return "Mock summary for math/analysis (Dev mode)."
    forecast = context.get("forecast") or {}
    forecast_note = ""
    if forecast.get("forecast") and forecast.get("stats"):
        forecast_note = f"\nNear-term prognosis (next 3 trading days, linear trend): {forecast.get('forecast')}. Stats: {forecast.get('stats')}."
    prompt = f"""You are a financial analysis sub-agent. Summarize the following mathematical/analytical data (prices, series, metrics) in 2-4 short sentences. Focus on: trend, volatility, key numbers; what the math suggests.{forecast_note} No advice yet—pure analysis.

Data:
{context}
"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    return result if result is not None else LLM_FALLBACK_MESSAGE


def run_keywords_sub_agent(symbol: str, session_context: dict[str, Any]) -> List[str]:
    """
    Derive dynamic search keywords for a stock from its context (name, sector, fundamentals).
    Returns a list of 5–10 short keywords/phrases for web search (commodities, sector, themes).
    """
    if get_settings().dev_mode:
        return ["commodity", "sector", "ETF"]
    ctx = session_context or {}
    fund = ctx.get("fundamentals") or ctx.get("scan_context", {}).get("fundamentals") or {}
    name = fund.get("Name") or fund.get("name") or ""
    sector = fund.get("Sector") or fund.get("sector") or ""
    industry = fund.get("Industry") or fund.get("industry") or ""
    parts = [f"Symbol: {symbol}"]
    if name:
        parts.append(f"Name: {name}")
    if sector:
        parts.append(f"Sector: {sector}")
    if industry:
        parts.append(f"Industry: {industry}")
    context_blob = "\n".join(parts)
    prompt = f"""You are a sub-agent that suggests web search keywords for a stock. Given the following stock context, output 5–10 short search keywords or phrases (one per line) that would help find relevant news and analysis. Include: underlying commodities or assets (e.g. silver, oil), sector/industry terms, ETF themes (e.g. leveraged, short), and related market terms. Output ONLY one keyword or short phrase per line, no numbering or bullets.

Stock context:
{context_blob}

Keywords (one per line):"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    if not result or not result.strip():
        return []
    keywords = []
    for line in result.strip().splitlines():
        # Strip numbering/bullets like "1.", "- ", "• "
        t = line.strip().lstrip("0123456789.-•) ").strip()
        if t and len(t) <= 80:
            keywords.append(t)
    logger.info("keywords sub-agent for %s returned %s terms", symbol, len(keywords))
    return keywords[:10]


def run_main_agent(summaries: dict[str, Optional[str]], symbol: str) -> Optional[str]:
    """Synthesize all sub-agent summaries into final financial advice. Returns markdown text."""
    if get_settings().dev_mode:
        return "Mock financial advice for Dev mode. No real LLM calls."
    parts = [f"- **{k}:** {v or 'N/A'}" for k, v in summaries.items() if v]
    combined = "\n".join(parts)
    prompt = f"""You are a financial advisor. Synthesize the following sub-analyses into one clear financial advice for the stock {symbol}. Include: how the stock behaves, how the analysis looks, whether one should consider buying or shorting (or holding), and the most likely near-term outlook. When a **Forecast** (next 3 trading days) is provided, use it to inform the near-term outlook. Write in clear, concise paragraphs. Always format your response in Markdown: use **bold** for emphasis, ## for section headers, and - or 1. for lists.
Sub-analyses:
{combined}
"""
    result = _invoke_llm([HumanMessage(content=prompt)])
    return result if result is not None else LLM_FALLBACK_MESSAGE


def run_main_agent_stream(
    summaries: dict[str, Optional[str]], symbol: str
) -> Generator[str, None, None]:
    """Stream main agent response token-by-token. Yields content chunks."""
    if get_settings().dev_mode:
        for c in "Mock financial advice for Dev mode. No real LLM calls.":
            yield c
        return
    parts = [f"- **{k}:** {v or 'N/A'}" for k, v in summaries.items() if v]
    combined = "\n".join(parts)
    prompt = f"""You are a financial advisor. Synthesize the following sub-analyses into one clear financial advice for the stock {symbol}. Include: how the stock behaves, how the analysis looks, whether one should consider buying or shorting (or holding), and the most likely near-term outlook. When a **Forecast** (next 3 trading days) is provided, use it to inform the near-term outlook. Write in clear, concise paragraphs. Always format your response in Markdown: use **bold** for emphasis, ## for section headers, and - or 1. for lists.
Sub-analyses:
{combined}
"""
    yielded_any = False
    for chunk in _stream_llm([HumanMessage(content=prompt)]):
        yielded_any = True
        yield chunk
    if not yielded_any:
        for c in (LLM_FALLBACK_MESSAGE or ""):
            yield c
