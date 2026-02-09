"""Yahoo Finance adapter: yfinance + ISIN search. No API key; fallback for Alpha Vantage."""
import logging
import os
from typing import Any, Optional

import requests

try:
    import yfinance as yf
except ImportError:
    yf = None

from app.adapters.base import DataSourceAdapter

logger = logging.getLogger(__name__)

YAHOO_SEARCH_URL = "https://query1.finance.yahoo.com/v1/finance/search"


def _yahoo_search(query: str, quotes_count: int = 10) -> Optional[dict[str, Any]]:
    """Search Yahoo Finance by query (ISIN or name). Returns {symbol, name} or None."""
    try:
        r = requests.get(
            YAHOO_SEARCH_URL,
            params={"q": query, "quotesCount": quotes_count},
            headers={"User-Agent": "Mozilla/5.0 (compatible; FinancialAssistant/1.0)"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        quotes = data.get("quotes") or []
        for q in quotes:
            sym = q.get("symbol")
            if not sym or not isinstance(sym, str) or not sym.strip():
                continue
            longname = (q.get("longname") or "").strip() or None
            shortname = (q.get("shortname") or "").strip() or None
            return {"symbol": sym.strip(), "name": longname or shortname or sym.strip()}
        return None
    except Exception:
        return None


def _isin_search(isin: str) -> Optional[dict[str, Any]]:
    return _yahoo_search(isin, quotes_count=5)


def _search_by_name(name: str) -> Optional[dict[str, Any]]:
    """Search by stock name. Tries full name with more results for better match."""
    return _yahoo_search(name, quotes_count=10)


class YahooFinanceAdapter(DataSourceAdapter):
    def resolve_isin(self, isin: str) -> Optional[dict[str, Any]]:
        return _isin_search(isin)

    def resolve_by_name(self, name: str) -> Optional[dict[str, Any]]:
        return _search_by_name(name)

    def get_quote(self, symbol: str) -> Optional[dict[str, Any]]:
        if not yf:
            return None
        try:
            t = yf.Ticker(symbol)
            info = t.info
            return {
                "symbol": symbol,
                "price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
            }
        except Exception:
            return None

    def get_series(
        self,
        symbol: str,
        data_type: str,
    ) -> Optional[list[dict[str, Any]]]:
        if not yf:
            return None
        # Request at least 1 year for daily (math analysis and forecast); weekly/monthly as needed
        period_map = {"daily": "2y", "weekly": "1y", "monthly": "2y"}
        period = period_map.get(data_type, "2y")
        try:
            t = yf.Ticker(symbol)
            df = t.history(period=period, interval="1d" if data_type == "daily" else "1wk")
            if df is None or df.empty:
                return None
            out = []
            for ts, row in df.iterrows():
                out.append({
                    "time": ts.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]) if "Open" in row else None,
                    "high": float(row["High"]) if "High" in row else None,
                    "low": float(row["Low"]) if "Low" in row else None,
                    "close": float(row["Close"]) if "Close" in row else None,
                    "volume": int(row["Volume"]) if "Volume" in row else None,
                })
            out.sort(key=lambda x: x["time"])
            return out
        except Exception:
            return None

    def get_fundamentals(self, symbol: str) -> Optional[dict[str, Any]]:
        if not yf:
            return None
        try:
            t = yf.Ticker(symbol)
            info = t.info
            if not info or info.get("symbol") != symbol:
                return None
            return {
                "Symbol": symbol,
                "Name": info.get("longName"),
                "MarketCapitalization": info.get("marketCap"),
                "PERatio": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
                "52WeekHigh": info.get("fiftyTwoWeekHigh"),
                "52WeekLow": info.get("fiftyTwoWeekLow"),
                "Beta": info.get("beta"),
                "DividendYield": info.get("dividendYield"),
                "DividendPerShare": info.get("dividendRate"),
                "ProfitMargin": info.get("profitMargins"),
                "OperatingMarginTTM": info.get("operatingMargins"),
                "ReturnOnAssetsTTM": info.get("returnOnAssets"),
                "ReturnOnEquityTTM": info.get("returnOnEquity"),
                "RevenueTTM": info.get("totalRevenue"),
                "GrossProfitTTM": info.get("grossProfits"),
                "Sector": info.get("sector"),
                "Industry": info.get("industry"),
                "Country": info.get("country"),
                "BookValue": info.get("bookValue"),
                "AnalystTargetPrice": info.get("targetMeanPrice"),
                "ShortRatio": info.get("shortRatio"),
                "ShortPercentOutstanding": info.get("shortPercentOfFloat"),
                "SharesOutstanding": info.get("sharesOutstanding"),
                "TrailingPE": info.get("trailingPE"),
                "ForwardPE": info.get("forwardPE"),
                "PEGRatio": info.get("pegRatio"),
                "PriceToBookRatio": info.get("priceToBook"),
                "QuarterlyEarningsGrowthYOY": info.get("earningsQuarterlyGrowth"),
                "QuarterlyRevenueGrowthYOY": info.get("revenueGrowth"),
            }
        except Exception:
            return None

    def get_news(self, symbol: str, limit: int = 10) -> Optional[list[dict[str, Any]]]:
        if not yf:
            return None
        raw: list[dict[str, Any]] = []
        try:
            t = yf.Ticker(symbol)
            # Prefer get_news(); fallback to .news (structure may differ by yfinance version)
            if hasattr(t, "get_news"):
                raw = t.get_news(count=limit) or []
            else:
                raw = (getattr(t, "news", None) or [])[:limit]
            if not raw:
                # Fallback: Search-based news (sometimes more reliable for ticker-specific news)
                try:
                    search = yf.Search(symbol, news_count=limit)
                    raw = getattr(search, "news", None) or []
                except Exception as e:
                    logger.debug("Yahoo Search news fallback failed symbol=%s: %s", symbol, e)
        except Exception as e:
            logger.warning("Yahoo get_news failed symbol=%s: %s", symbol, e)
            return None
        def _str_url(v: Any) -> Optional[str]:
            if v is None:
                return None
            if isinstance(v, str) and v.startswith("http"):
                return v
            if isinstance(v, dict) and v.get("url"):
                return str(v["url"]).strip()
            s = str(v).strip()
            return s if s.startswith("http") else None

        def _str_time(v: Any) -> Optional[str]:
            if v is None:
                return None
            if isinstance(v, str):
                return v
            if isinstance(v, (int, float)):
                return str(v)
            return str(v) if v else None

        out = []
        for n in raw:
            # New yfinance: item has id + content dict with title, summary, pubDate, canonicalUrl, etc.
            content = n.get("content") if isinstance(n.get("content"), dict) else n
            title = content.get("title") or n.get("title")
            url = _str_url(
                content.get("canonicalUrl")
                or content.get("clickThroughUrl")
                or n.get("link")
                or n.get("url")
            )
            summary = content.get("summary") or content.get("description") or n.get("summary")
            time_pub = _str_time(
                content.get("pubDate")
                or content.get("displayTime")
                or n.get("providerPublishTime")
                or n.get("time_published")
            )
            if title or summary or url:
                out.append({
                    "title": str(title) if title else None,
                    "url": url,
                    "summary": str(summary)[:2000] if summary else None,
                    "time_published": time_pub,
                })
        if not out:
            logger.debug("Yahoo get_news returned no usable items symbol=%s", symbol)
            return None
        logger.info("Yahoo get_news symbol=%s items=%s", symbol, len(out))
        return out
