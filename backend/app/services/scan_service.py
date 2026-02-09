"""Scan service: resolve ISIN -> symbol; fetch/cache quote, series, fundamentals, news per scan.md."""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session as DBSession

logger = logging.getLogger(__name__)

from app.adapters.alpha_vantage import AlphaVantageAdapter
from app.adapters.base import DataSourceAdapter
from app.adapters.yahoo import YahooFinanceAdapter
from app.config import get_settings
from app.models.base import OHLCV, ScanCache, Stock, SymbolResolution


def _mock_quote(symbol: str = "MOCK") -> dict:
    return {"symbol": symbol, "price": 100.0, "volume": 1_000_000, "change": 1.0, "change_percent": "1.0%"}


def _mock_series(count: int = 10) -> list[dict]:
    base = datetime.now(timezone.utc).date()
    return [
        {
            "time": (base - timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": 99.0 - i,
            "high": 101.0 + i,
            "low": 98.0 - i,
            "close": 100.0,
            "volume": 1_000_000,
        }
        for i in range(count, 0, -1)
    ]


def _mock_fundamentals(symbol: str = "MOCK") -> dict:
    return {
        "Symbol": symbol,
        "Name": "Mock Company (Dev)",
        "MarketCapitalization": "1000000000",
        "PERatio": "15",
        "EPS": "1.5",
        "52WeekHigh": "120",
        "52WeekLow": "80",
    }


def _mock_news() -> list[dict]:
    return [
        {
            "title": "Mock news (Dev mode)",
            "url": "",
            "summary": "No real API calls in Dev mode.",
            "time_published": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M00"),
        }
    ]

# TTLs from scan.md (seconds)
TTL_QUOTE = 15 * 60
TTL_DAILY = 7 * 24 * 3600
TTL_WEEKLY = 7 * 24 * 3600
TTL_MONTHLY = 7 * 24 * 3600
TTL_FUNDAMENTALS = 7 * 24 * 3600
TTL_NEWS = 3600
TTL_ISIN = 30 * 24 * 3600

DATA_TYPES = ["quote", "daily", "weekly", "monthly", "fundamentals", "news"]


def _ttl_seconds(data_type: str) -> int:
    return {
        "quote": TTL_QUOTE,
        "daily": TTL_DAILY,
        "weekly": TTL_WEEKLY,
        "monthly": TTL_MONTHLY,
        "fundamentals": TTL_FUNDAMENTALS,
        "news": TTL_NEWS,
    }.get(data_type, TTL_DAILY)


def _now() -> datetime:
    """UTC now, timezone-aware so it can be compared with DB timestamps (TIMESTAMPTZ)."""
    return datetime.now(timezone.utc)


def _name_search_variants(name: str) -> list[str]:
    """Build name variants for symbol search: full name, without parenthetical, shorter."""
    variants = []
    s = (name or "").strip()
    if not s:
        return variants
    variants.append(s)
    # Without parenthetical part e.g. " (Acc)" or " (EUR Hedged)"
    no_paren = re.sub(r"\s*\([^)]*\)\s*", " ", s).strip()
    if no_paren and no_paren != s:
        variants.append(no_paren)
    # First 2–3 words (e.g. "Physical Gold USD" -> "Physical Gold")
    words = s.split()
    if len(words) > 2:
        variants.append(" ".join(words[:2]))
    if len(words) > 3 and " ".join(words[:3]) not in variants:
        variants.append(" ".join(words[:3]))
    return variants


class ScanService:
    def __init__(self, db: DBSession):
        self.db = db
        self._adapters: list[DataSourceAdapter] = [
            AlphaVantageAdapter(),
            YahooFinanceAdapter(),
        ]

    def resolve_isin(self, isin: str) -> Optional[str]:
        """Resolve ISIN to symbol. Uses DB cache, then adapters (ISIN search, then name fallback). Returns symbol or None."""
        # In dev_mode still use DB first so that previously fetched data is shown from local DB
        row = self.db.query(SymbolResolution).filter(SymbolResolution.isin == isin).first()
        if row:
            if get_settings().dev_mode:
                logger.debug("dev_mode: resolve_isin from DB isin=%s symbol=%s", isin, row.symbol)
                return row.symbol
            cutoff = _now() - timedelta(seconds=TTL_ISIN)
            if row.updated_at and row.updated_at >= cutoff:
                logger.info("resolve_isin cache hit isin=%s symbol=%s", isin, row.symbol)
                return row.symbol
        elif get_settings().dev_mode:
            mock_symbol = "MOCK" if len(isin) > 6 or " " in isin else (isin[:4].upper() if isin else "MOCK")
            logger.info("dev_mode: resolve_isin mock symbol=%s (no DB resolution)", mock_symbol)
            return mock_symbol
        logger.debug("resolve_isin cache miss or expired isin=%s", isin)
        # Try adapters: first by ISIN
        for adapter in self._adapters:
            if hasattr(adapter, "resolve_isin") and adapter.resolve_isin:
                result = adapter.resolve_isin(isin)
                if result and result.get("symbol"):
                    logger.info("resolve_isin resolved by ISIN isin=%s symbol=%s", isin, result["symbol"])
                    return self._persist_resolution(isin, result, adapter)
        # Fallback: resolve by stock name from DB (try full name and shorter variants)
        stock = self.db.query(Stock).filter(Stock.isin == isin).first()
        if stock and stock.name:
            name_variants = _name_search_variants(stock.name)
            for adapter in self._adapters:
                if not hasattr(adapter, "resolve_by_name") or not adapter.resolve_by_name:
                    continue
                for name in name_variants:
                    result = adapter.resolve_by_name(name)
                    if result and result.get("symbol"):
                        logger.info("resolve_isin resolved by name isin=%s name=%s symbol=%s", isin, name, result["symbol"])
                        return self._persist_resolution(isin, result, adapter)
        logger.warning("resolve_isin failed isin=%s", isin)
        return None

    def _persist_resolution(self, isin: str, result: dict, adapter: DataSourceAdapter) -> str:
        """Persist symbol resolution and return symbol."""
        symbol = result["symbol"]
        name = result.get("name")
        source = getattr(adapter.__class__, "__name__", None) or "unknown"
        existing = self.db.query(SymbolResolution).filter(SymbolResolution.isin == isin).first()
        if existing:
            existing.symbol = symbol
            existing.name = name or existing.name
            existing.source = source
            existing.updated_at = _now()
        else:
            self.db.add(SymbolResolution(
                isin=isin,
                symbol=symbol,
                name=name,
                source=source,
            ))
        self.db.commit()
        return symbol

    def _get_cached(self, symbol: str, data_type: str, interval: str = "") -> Optional[dict]:
        row = self.db.query(ScanCache).filter(
            ScanCache.symbol == symbol,
            ScanCache.data_type == data_type,
            ScanCache.interval == (interval or ""),
        ).first()
        if not row:
            return None
        ttl = _ttl_seconds(data_type)
        fetched = row.fetched_at
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        if (_now() - fetched).total_seconds() > ttl:
            return None
        logger.debug("scan_cache hit symbol=%s data_type=%s", symbol, data_type)
        return row.payload

    def _set_cached(self, symbol: str, data_type: str, payload: dict, interval: str = "") -> None:
        from sqlalchemy import update
        existing = self.db.query(ScanCache).filter(
            ScanCache.symbol == symbol,
            ScanCache.data_type == data_type,
            ScanCache.interval == (interval or ""),
        ).first()
        if existing:
            existing.payload = payload
            existing.fetched_at = _now()
        else:
            self.db.add(ScanCache(
                symbol=symbol,
                data_type=data_type,
                interval=interval or "",
                payload=payload,
                fetched_at=_now(),
            ))
        self.db.commit()

    def _get_ohlcv_cached(self, symbol: str, data_type: str) -> Optional[list[dict]]:
        row = self.db.query(ScanCache).filter(
            ScanCache.symbol == symbol,
            ScanCache.data_type == data_type,
            ScanCache.interval == "",
        ).first()
        if not row:
            return None
        ttl = _ttl_seconds(data_type)
        fetched = row.fetched_at
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        if (_now() - fetched).total_seconds() > ttl:
            return None
        logger.debug("scan_cache hit OHLCV symbol=%s data_type=%s", symbol, data_type)
        return row.payload.get("series") if isinstance(row.payload, dict) else row.payload

    def _set_ohlcv_cached(self, symbol: str, data_type: str, series: list[dict]) -> None:
        payload = {"series": series}
        self._set_cached(symbol, data_type, payload, "")

    def _fetch_quote(self, symbol: str) -> Optional[dict]:
        for adapter in self._adapters:
            try:
                out = adapter.get_quote(symbol)
                if out:
                    return out
            except Exception:
                continue
        return None

    def _fetch_series(self, symbol: str, data_type: str) -> Optional[list[dict]]:
        for adapter in self._adapters:
            try:
                out = adapter.get_series(symbol, data_type)
                if out:
                    return out
            except Exception:
                continue
        return None

    def _fetch_fundamentals(self, symbol: str) -> Optional[dict]:
        for adapter in self._adapters:
            try:
                out = adapter.get_fundamentals(symbol)
                if out:
                    return out
            except Exception:
                continue
        return None

    def _fetch_news(self, symbol: str, limit: int = 10) -> Optional[list]:
        for adapter in self._adapters:
            try:
                out = adapter.get_news(symbol, limit=limit)
                if out:
                    return out
            except Exception as e:
                logger.debug("news fetch failed adapter=%s symbol=%s: %s", type(adapter).__name__, symbol, e)
                continue
        return None

    def scan(
        self,
        identifier: str,
        *,
        on_progress: Optional[Callable[[str, int, int, Optional[str]], None]] = None,
    ) -> dict[str, Any]:
        """
        Scan all data for identifier (ISIN or symbol). Resolves ISIN -> symbol.
        on_progress(step_name, step_index, total_steps, error_message).
        Returns aggregated context: { symbol, quote, daily, weekly, monthly, fundamentals, news }.
        """
        if get_settings().dev_mode:
            symbol = identifier if (identifier.isupper() and len(identifier) <= 6 and " " not in identifier) else self.resolve_isin(identifier)
            if not symbol:
                return {"symbol": None, "error": "Could not resolve identifier to symbol"}
            # Prefer cached data from DB so dev shows previously fetched data
            result_dev: dict[str, Any] = {"symbol": symbol, "quote": None, "daily": None, "weekly": None, "monthly": None, "fundamentals": None, "news": None}
            result_dev["quote"] = self._get_cached(symbol, "quote") or _mock_quote(symbol)
            result_dev["daily"] = self._get_ohlcv_cached(symbol, "daily") or _mock_series(252)
            result_dev["weekly"] = self._get_ohlcv_cached(symbol, "weekly") or _mock_series(52)
            result_dev["monthly"] = self._get_ohlcv_cached(symbol, "monthly") or _mock_series(12)
            result_dev["fundamentals"] = self._get_cached(symbol, "fundamentals") or _mock_fundamentals(symbol)
            news_cached = self._get_cached(symbol, "news")
            result_dev["news"] = (news_cached.get("items") if isinstance(news_cached, dict) else news_cached) if news_cached else _mock_news()
            total_steps = 7
            for s in range(1, total_steps + 1):
                if on_progress:
                    on_progress("Mock step", s, total_steps, None)
            logger.info("dev_mode: scan returning context symbol=%s (from DB when available)", symbol)
            return result_dev
        total_steps = 7
        step = 0
        symbol: Optional[str] = None
        if identifier.isupper() and len(identifier) <= 6 and " " not in identifier:
            symbol = identifier
        else:
            step += 1
            if on_progress:
                on_progress("Resolving symbol", step, total_steps, None)
            symbol = self.resolve_isin(identifier)
            if not symbol:
                if on_progress:
                    on_progress("Resolving symbol", step, total_steps, "Could not resolve ISIN to symbol")
                return {"symbol": None, "error": "Could not resolve identifier to symbol"}

        result: dict[str, Any] = {"symbol": symbol, "quote": None, "daily": None, "weekly": None, "monthly": None, "fundamentals": None, "news": None}

        # Quote
        step += 1
        if on_progress:
            on_progress("Fetching price data", step, total_steps, None)
        cached = self._get_cached(symbol, "quote")
        if cached:
            result["quote"] = cached
            logger.info("scan quote cache hit symbol=%s", symbol)
        else:
            quote = self._fetch_quote(symbol)
            if quote:
                self._set_cached(symbol, "quote", quote)
                result["quote"] = quote
                logger.info("scan quote fetched symbol=%s", symbol)
            else:
                logger.warning("scan quote fetch failed symbol=%s", symbol)
                if on_progress:
                    on_progress("Fetching price data", step, total_steps, "Quote fetch failed")

        # Daily
        step += 1
        if on_progress:
            on_progress("Fetching daily series", step, total_steps, None)
        cached = self._get_ohlcv_cached(symbol, "daily")
        if cached:
            result["daily"] = cached
            logger.info("scan daily cache hit symbol=%s", symbol)
        else:
            series = self._fetch_series(symbol, "daily")
            if series:
                self._set_ohlcv_cached(symbol, "daily", series)
                result["daily"] = series
                logger.info("scan daily fetched symbol=%s points=%s", symbol, len(series))
            else:
                logger.warning("scan daily fetch failed symbol=%s", symbol)
                if on_progress:
                    on_progress("Fetching daily series", step, total_steps, "Daily series fetch failed")

        # Fundamentals
        step += 1
        if on_progress:
            on_progress("Fetching fundamentals", step, total_steps, None)
        cached = self._get_cached(symbol, "fundamentals")
        if cached:
            result["fundamentals"] = cached
            logger.info("scan fundamentals cache hit symbol=%s", symbol)
        else:
            fund = self._fetch_fundamentals(symbol)
            if fund:
                self._set_cached(symbol, "fundamentals", fund)
                result["fundamentals"] = fund
                logger.info("scan fundamentals fetched symbol=%s", symbol)
            else:
                logger.warning("scan fundamentals fetch failed symbol=%s", symbol)
                if on_progress:
                    on_progress("Fetching fundamentals", step, total_steps, "Fundamentals fetch failed")

        # News
        step += 1
        if on_progress:
            on_progress("Fetching news", step, total_steps, None)
        cached = self._get_cached(symbol, "news")
        if cached:
            result["news"] = cached.get("items") if isinstance(cached, dict) else cached
            logger.info("scan news cache hit symbol=%s", symbol)
        else:
            news = self._fetch_news(symbol, limit=10)
            if news:
                self._set_cached(symbol, "news", {"items": news})
                result["news"] = news
                logger.info("scan news fetched symbol=%s items=%s", symbol, len(news))
            else:
                logger.warning("scan news fetch failed symbol=%s", symbol)
                if on_progress:
                    on_progress("Fetching news", step, total_steps, "News fetch failed")

        if on_progress:
            on_progress("Scan complete", total_steps, total_steps, None)
        return result

    def get_series(self, identifier: str, interval: str) -> Optional[list[dict]]:
        """Get OHLCV series for graph. interval: 1d, 1w, 1m -> daily, weekly, monthly. Prefer DB in dev_mode."""
        symbol = self.resolve_isin(identifier) if not (identifier.isupper() and len(identifier) <= 6) else identifier
        if not symbol:
            return None
        data_type = {"1d": "daily", "1w": "weekly", "1m": "monthly"}.get(interval, "daily")
        cached = self._get_ohlcv_cached(symbol, data_type)
        if cached:
            if get_settings().dev_mode:
                logger.debug("dev_mode: get_series from DB symbol=%s data_type=%s points=%s", symbol, data_type, len(cached))
            return cached
        if get_settings().dev_mode:
            # No cached data in dev: return 1 year of mock points so graph/forecast work
            n = 252 if data_type == "daily" else 52 if data_type == "weekly" else 12
            return _mock_series(n)
        series = self._fetch_series(symbol, data_type)
        if series:
            self._set_ohlcv_cached(symbol, data_type, series)
        return series

    def get_metrics(self, identifier: str) -> Optional[dict]:
        """Get fundamentals for metrics panel. Prefer DB in dev_mode."""
        symbol = self.resolve_isin(identifier) if not (identifier.isupper() and len(identifier) <= 6) else identifier
        if not symbol:
            return None
        cached = self._get_cached(symbol, "fundamentals")
        if cached:
            if get_settings().dev_mode:
                logger.debug("dev_mode: get_metrics from DB symbol=%s", symbol)
            return cached
        if get_settings().dev_mode:
            return _mock_fundamentals(symbol)
        fund = self._fetch_fundamentals(symbol)
        if fund:
            self._set_cached(symbol, "fundamentals", fund)
        return fund
