"""Alpha Vantage REST adapter. Uses ALPHA_VANTAGE_API_KEY; respects rate limiter."""
import logging
import os
import time
from typing import Any, Optional

import requests

from app.adapters.base import DataSourceAdapter
from app.services.rate_limiter import get_alpha_vantage_limiter

logger = logging.getLogger(__name__)
BASE_URL = "https://www.alphavantage.co/query"


def _to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _to_int(val: Any) -> Optional[int]:
    n = _to_float(val)
    return int(n) if n is not None else None


def _get_api_key() -> Optional[str]:
    return os.getenv("ALPHA_VANTAGE_API_KEY")


def _request(params: dict[str, str]) -> Optional[dict[str, Any]]:
    key = _get_api_key()
    if not key:
        return None
    limiter = get_alpha_vantage_limiter()
    if not limiter.can_call():
        return None
    params["apikey"] = key
    try:
        limiter.record_call()
        r = requests.get(BASE_URL, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "Error Message" in data or "Note" in data:
            logger.debug("Alpha Vantage rate limit or error response; skipping")
            return None
        return data
    except Exception:
        return None


class AlphaVantageAdapter(DataSourceAdapter):
    def resolve_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """Resolve stock name to ticker using SYMBOL_SEARCH. Returns {symbol, name} or None."""
        data = _request({"function": "SYMBOL_SEARCH", "keywords": name, "datatype": "json"})
        if not data or "bestMatches" not in data:
            return None
        matches = data.get("bestMatches") or []
        for m in matches:
            symbol = m.get("1. symbol")
            if symbol and isinstance(symbol, str) and symbol.strip():
                return {
                    "symbol": symbol.strip(),
                    "name": (m.get("2. name") or symbol).strip() if isinstance(m.get("2. name"), str) else symbol.strip(),
                }
        return None

    def get_quote(self, symbol: str) -> Optional[dict[str, Any]]:
        data = _request({"function": "GLOBAL_QUOTE", "symbol": symbol})
        if not data or "Global Quote" not in data:
            return None
        gq = data["Global Quote"]
        return {
            "symbol": gq.get("01. symbol"),
            "price": gq.get("05. price"),
            "volume": gq.get("06. volume"),
            "change": gq.get("09. change"),
            "change_percent": gq.get("10. change percent"),
        }

    def get_series(
        self,
        symbol: str,
        data_type: str,
    ) -> Optional[list[dict[str, Any]]]:
        func_map = {
            "daily": "TIME_SERIES_DAILY",
            "weekly": "TIME_SERIES_WEEKLY",
            "monthly": "TIME_SERIES_MONTHLY",
        }
        func = func_map.get(data_type)
        if not func:
            return None
        outputsize = "full" if data_type == "daily" else "compact"
        data = _request({"function": func, "symbol": symbol, "outputsize": outputsize})
        if not data:
            return None
        key = next((k for k in data if "Time Series" in k), None)
        if not key:
            return None
        series = data[key]
        out = []
        for date_str, v in series.items():
            open_ = _to_float(v.get("1. open"))
            high = _to_float(v.get("2. high"))
            low = _to_float(v.get("3. low"))
            close = _to_float(v.get("4. close"))
            vol = _to_int(v.get("5. volume"))
            out.append({
                "time": date_str,
                "open": open_,
                "high": high,
                "low": low,
                "close": close,
                "volume": vol,
            })
        out.sort(key=lambda x: x["time"])
        return out

    def get_fundamentals(self, symbol: str) -> Optional[dict[str, Any]]:
        data = _request({"function": "OVERVIEW", "symbol": symbol})
        if not data:
            return None
        if not data.get("Symbol"):
            data["Symbol"] = symbol
        etf_data = _request({"function": "ETF_PROFILE", "symbol": symbol})
        if etf_data and isinstance(etf_data, dict):
            for k, v in etf_data.items():
                if k not in data and v is not None and v != "":
                    data[k] = v
        return data

    def get_news(self, symbol: str, limit: int = 10) -> Optional[list[dict[str, Any]]]:
        from datetime import datetime, timedelta
        if not _get_api_key():
            logger.debug("Alpha Vantage get_news skipped: no API key")
            return None
        time_to = datetime.utcnow()
        time_from = time_to - timedelta(days=7)
        data = _request({
            "function": "NEWS_SENTIMENT",
            "tickers": symbol,
            "limit": str(min(limit, 50)),
            "time_from": time_from.strftime("%Y%m%dT%H%M00"),
            "time_to": time_to.strftime("%Y%m%dT%H%M00"),
        })
        if not data:
            logger.debug("Alpha Vantage get_news no response symbol=%s", symbol)
            return None
        if "feed" not in data:
            if "Error Message" in data:
                logger.debug("Alpha Vantage get_news error symbol=%s: %s", symbol, data.get("Error Message"))
            elif "Note" in data:
                logger.debug("Alpha Vantage get_news rate limit or note symbol=%s", symbol)
            return None
        feed = data["feed"][:limit]
        out = [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "summary": item.get("summary"),
                "time_published": item.get("time_published"),
                "sentiment_score": item.get("overall_sentiment_score"),
            }
            for item in feed
        ]
        logger.info("Alpha Vantage get_news symbol=%s items=%s", symbol, len(out))
        return out
