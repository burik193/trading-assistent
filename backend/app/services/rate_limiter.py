"""Alpha Vantage rate limiter: 5/min, 25/day. Fallback to Yahoo when capped."""
import time
from datetime import datetime, timedelta
from threading import Lock

# Free tier: 25 requests per day, 5 per minute
MIN_INTERVAL_SECONDS = 12  # ~5 per minute
DAILY_LIMIT = 25


class AlphaVantageRateLimiter:
    def __init__(self):
        self._lock = Lock()
        self._last_call_time: float = 0.0
        self._daily_count = 0
        self._daily_reset_date: str = datetime.utcnow().strftime("%Y-%m-%d")

    def _maybe_reset_daily(self) -> None:
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._daily_reset_date:
            self._daily_reset_date = today
            self._daily_count = 0

    def can_call(self) -> bool:
        """Return True if we can make an Alpha Vantage call (under daily limit)."""
        with self._lock:
            self._maybe_reset_daily()
            return self._daily_count < DAILY_LIMIT

    def record_call(self) -> None:
        """Record that we made a call; enforce min interval."""
        with self._lock:
            self._maybe_reset_daily()
            now = time.monotonic()
            elapsed = now - self._last_call_time
            if elapsed < MIN_INTERVAL_SECONDS:
                time.sleep(MIN_INTERVAL_SECONDS - elapsed)
            self._last_call_time = time.monotonic()
            self._daily_count += 1


# Singleton for use by scan service and Alpha Vantage adapter
_limiter: AlphaVantageRateLimiter | None = None


def get_alpha_vantage_limiter() -> AlphaVantageRateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = AlphaVantageRateLimiter()
    return _limiter
