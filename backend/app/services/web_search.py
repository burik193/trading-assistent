"""Web search for stocks/commodities/news. Used by chat when context is insufficient.

Unified flow: (1) Structured financial news API (ticker-specific), (2) RSS feeds, (3) DuckDuckGo fallback.
Search terms: symbol + static keywords (from name/sector) + dynamic keywords from keywords sub-agent.
"""
import logging
import re
from typing import Any, Optional
from urllib.parse import quote_plus

import requests

from app.agent.sub_agents import run_keywords_sub_agent

logger = logging.getLogger(__name__)

# Fallback when keywords sub-agent is unavailable or returns few terms
COMMODITY_KEYWORDS = (
    "silver", "gold", "oil", "copper", "bitcoin", "crypto", "wheat", "natural gas",
)
MAX_RESULTS_PER_QUERY = 5
MAX_TOTAL_SNIPPETS = 15
MAX_SUGGESTED_TERMS = 12

# === Extendable sources ===

# NewsData.io: Latest endpoint (past 48h). GET, q=keyword. Free: 10/request, paid: 50.
# Docs: https://newsdata.io/documentation
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/latest"


def fetch_from_financial_news_api(symbol: str, api_key: str) -> list[dict[str, str]]:
    """
    Fetch news from NewsData.io Latest API (https://newsdata.io/documentation).
    Uses GET .../latest?apikey=KEY&q=QUERY&language=en. Returns list of {title, body, url}.
    """
    if not symbol or not api_key:
        return []

    params = {
        "apikey": api_key,
        "q": symbol,
        "language": "en",
    }
    # Free tier: max 10/request; paid: up to 50. Request only what we need.
    size = min(MAX_RESULTS_PER_QUERY, 10)
    params["size"] = size

    try:
        r = requests.get(NEWSDATA_BASE_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        # Response: status, totalResults, results (array of articles)
        articles = data.get("results") or []
    except requests.RequestException as e:
        logger.warning("NewsData.io request failed: %s", e)
        return []
    except (ValueError, KeyError) as e:
        logger.warning("NewsData.io response parse error: %s", e)
        return []

    results = []
    for article in articles:
        title = (article.get("title") or "").strip()
        link = (article.get("link") or "").strip()
        desc = (article.get("description") or article.get("content") or "").strip()
        if desc:
            desc = desc[:500]
        results.append({"title": title, "body": desc, "url": link})
    logger.debug("NewsData.io returned %s articles for q=%s", len(results), symbol)
    return results


def fetch_rss_feeds(keywords: str, max_results: int = 5) -> list[dict[str, str]]:
    """
    Search RSS feeds for keyword mentions (e.g. Google News RSS).
    Returns list of {title, body, url}.
    """
    try:
        import feedparser
    except ImportError:
        logger.debug("feedparser not installed; skipping RSS")
        return []
    try:
        encoded = quote_plus(keywords)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
        feed = feedparser.parse(url, request_headers={"User-Agent": "FinancialAssistant/1.0"})
        items = (feed.entries or [])[:max_results]
    except Exception as e:
        logger.warning("RSS feed parse failed: %s", e)
        return []

    out = []
    for item in items:
        out.append({
            "title": (item.get("title") or "").strip(),
            "body": (item.get("summary") or item.get("description") or "").strip()[:500],
            "url": (item.get("link") or "").strip(),
        })
    return out


def _get_ddgs():
    """Return DDGS class from duckduckgo_search or ddgs package. Returns None if not installed."""
    try:
        from duckduckgo_search import DDGS
        return DDGS
    except ImportError:
        try:
            from ddgs import DDGS
            return DDGS
        except ImportError:
            return None


def _try_ddgs_news(keywords: str, max_results: int = 5) -> list[dict[str, str]]:
    """DuckDuckGo News fallback. Returns list of {title, body, url}."""
    DDGS = _get_ddgs()
    if not DDGS:
        return []
    try:
        results = list(DDGS().news(keywords, max_results=max_results, timelimit="m"))
        out = []
        for r in results:
            out.append({
                "title": (r.get("title") or "").strip(),
                "body": (r.get("body") or "").strip()[:500],
                "url": (r.get("url") or r.get("href") or "").strip(),
            })
        return out
    except Exception as e:
        logger.warning("DuckDuckGo news search failed: %s", e)
        return []


def search_web(
    queries: list[str],
    symbol: Optional[str] = None,
    financial_news_api_key: Optional[str] = None,
) -> str:
    """
    Unified search: (1) Financial News API (ticker-specific) → (2) RSS feeds → (3) DDG fallback.
    Returns a single string of concatenated snippets for the model.
    """
    if not queries:
        return ""

    seen_urls: set[str] = set()
    snippets: list[str] = []
    total_snippets = 0

    # 1) Try structured financial news (ticker specific)
    if symbol and financial_news_api_key:
        logger.info("Trying structured financial news API for %s …", symbol)
        articles = fetch_from_financial_news_api(symbol, financial_news_api_key)
        for art in articles:
            url = art.get("url", "").strip()
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = art.get("title", "")
            body = art.get("body", "") or ""
            snippets.append(f"- **{title}**\n  {body}\n  Source: {url}")
            total_snippets += 1
            if total_snippets >= MAX_TOTAL_SNIPPETS:
                break

    # 2) Try RSS feed search on all queries
    for q in queries:
        if total_snippets >= MAX_TOTAL_SNIPPETS:
            break
        q = (q or "").strip()
        if not q:
            continue
        try:
            rss_results = fetch_rss_feeds(q, max_results=MAX_RESULTS_PER_QUERY)
            for r in rss_results:
                url = r.get("url", "").strip()
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    snippets.append(
                        f"- **{r.get('title', '')}**\n  {r.get('body', '')}\n  Source: {url}"
                    )
                    total_snippets += 1
                    if total_snippets >= MAX_TOTAL_SNIPPETS:
                        break
        except Exception as e:
            logger.warning("RSS processing failed: %s", e)

    # 3) Fall back to DDG news search
    for q in queries:
        if total_snippets >= MAX_TOTAL_SNIPPETS:
            break
        q = (q or "").strip()
        if not q:
            continue
        news_results = _try_ddgs_news(q, max_results=MAX_RESULTS_PER_QUERY)
        for r in news_results:
            url = (r.get("url") or "").strip()
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            snippet_text = (
                f"- **{r.get('title', '')}**\n  {r.get('body', '')}\n  Source: {url or 'N/A'}"
            )
            snippets.append(snippet_text)
            total_snippets += 1
            if total_snippets >= MAX_TOTAL_SNIPPETS:
                break

    if not snippets:
        logger.info("search_web no results for queries=%s", queries)
        return "No web results found for the given queries."

    logger.info("search_web found %s snippets", len(snippets))
    return "\n\n".join(snippets)


def suggest_search_terms_from_context(session_context: dict[str, Any], symbol: str) -> list[str]:
    """
    Suggest search terms: symbol, static keywords from name/sector/commodity list,
    and dynamic keywords from the keywords sub-agent (LLM-derived for the given stock).
    """
    terms = []
    if symbol and isinstance(symbol, str) and len(symbol) <= 20:
        terms.append(symbol)
    ctx = session_context or {}
    fund = ctx.get("fundamentals") or {}
    name = fund.get("Name") or fund.get("name")
    if not name and isinstance(ctx.get("symbol"), str):
        name = ctx.get("symbol")
    if name and isinstance(name, str):
        name_lower = name.lower()
        for kw in COMMODITY_KEYWORDS:
            if kw in name_lower:
                terms.append(kw)
        words = re.sub(r"[^\w\s]", " ", name).split()
        if words:
            terms.append(" ".join(words[:3]))
    sector = fund.get("Sector") or fund.get("sector")
    if sector and isinstance(sector, str) and sector.strip():
        terms.append(sector.strip())
    # Dynamic keywords from sub-agent (commodities, sector, themes for this stock)
    try:
        dynamic = run_keywords_sub_agent(symbol or "", ctx)
        terms.extend(dynamic)
    except Exception as e:
        logger.debug("keywords sub-agent failed, using static terms only: %s", e)
    seen = set()
    out = []
    for t in terms:
        t = (t or "").strip()
        if t and t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out[:MAX_SUGGESTED_TERMS]
