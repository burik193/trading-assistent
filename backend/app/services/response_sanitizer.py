"""Sanitize API responses so provider/blocker messages are never sent to the client."""
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Generic message returned when data is considered unsafe (e.g. rate-limit text leaked)
DATA_UNAVAILABLE_MESSAGE = "Data temporarily unavailable for this symbol."

# Phrases that indicate provider error/rate-limit content; if found in string values, treat as blocker
BLOCKER_PHRASES = (
    "rate limit",
    "api key",
    "alphavantage.co/premium",
    "error message",
    "please subscribe",
)


def _contains_blocker_text(s: str) -> bool:
    if not s or not isinstance(s, str):
        return False
    lower = s.lower()
    return any(phrase in lower for phrase in BLOCKER_PHRASES)


def _dict_contains_blocker(obj: dict) -> bool:
    """Return True if dict has blocker keys or any string value with blocker phrases."""
    if "Note" in obj or "Error Message" in obj:
        return True
    for v in obj.values():
        if isinstance(v, str) and _contains_blocker_text(v):
            return True
        if isinstance(v, dict) and _dict_contains_blocker(v):
            return True
        if isinstance(v, list):
            for item in v:
                if isinstance(item, dict) and _dict_contains_blocker(item):
                    return True
                if isinstance(item, str) and _contains_blocker_text(item):
                    return True
    return False


def _list_contains_blocker(items: list) -> bool:
    """Return True if list contains any dict or string with blocker content."""
    for item in items:
        if isinstance(item, dict) and _dict_contains_blocker(item):
            return True
        if isinstance(item, str) and _contains_blocker_text(item):
            return True
    return False


def is_safe_metrics(metrics: dict[str, Any] | None) -> bool:
    """Return False if metrics payload contains provider/blocker content."""
    if not metrics or not isinstance(metrics, dict):
        return True
    return not _dict_contains_blocker(metrics)


def is_safe_series(series: list[dict] | None) -> bool:
    """Return False if series payload contains provider/blocker content."""
    if not series or not isinstance(series, list):
        return True
    return not _list_contains_blocker(series)
