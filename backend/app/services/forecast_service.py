"""Time series analysis: trend line, standard deviation bands, and short-term prognosis (next 3 days)."""
import logging
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Number of trading days to forecast
FORECAST_DAYS = 3
# Number of standard deviations for bands (e.g. 2 ≈ 95% under normality)
STD_BANDS_K = 2.0


def _parse_date(s: str) -> Optional[datetime]:
    """Parse YYYY-MM-DD to date."""
    try:
        return datetime.strptime(s[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _next_trading_days(from_date: datetime, count: int) -> list[str]:
    """Return next `count` trading days (skip Sat/Sun) as YYYY-MM-DD."""
    out: list[str] = []
    d = from_date.date()
    while len(out) < count:
        d += timedelta(days=1)
        if d.weekday() < 5:  # Mon=0 .. Fri=4
            out.append(d.strftime("%Y-%m-%d"))
    return out


def _linear_regression(x: list[float], y: list[float]) -> tuple[float, float]:
    """Ordinary least squares: y = intercept + slope * x. Returns (slope, intercept)."""
    n = len(x)
    if n < 2 or n != len(y):
        return 0.0, (y[0] if y else 0.0)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_xx = sum(xi * xi for xi in x)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    denom = n * sum_xx - sum_x * sum_x
    if abs(denom) < 1e-20:
        return 0.0, sum_y / n
    slope = (n * sum_xy - sum_x * sum_y) / denom
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def _sample_std(values: list[float]) -> float:
    """Sample standard deviation (Bessel correction)."""
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / (n - 1)
    return variance ** 0.5


def compute_forecast(series: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Compute trend line, standard deviation bands, and next 3 days forecast from daily OHLCV series.
    series: list of { time, open, high, low, close, volume } sorted by time ascending.
    Returns:
      trend_line: list of { time, value }
      upper_band, lower_band: list of { time, value } (trend ± k*std)
      forecast: list of { time, close } for next 3 trading days
      stats: { slope, intercept, std, last_date }
    """
    if not series or len(series) < 2:
        return {
            "trend_line": [],
            "upper_band": [],
            "lower_band": [],
            "forecast": [],
            "stats": {},
        }

    closes = []
    times = []
    for p in series:
        t = p.get("time")
        c = p.get("close")
        if t is not None and c is not None:
            try:
                closes.append(float(c))
            except (TypeError, ValueError):
                continue
            times.append(str(t)[:10])

    if len(closes) < 2:
        return {
            "trend_line": [],
            "upper_band": [],
            "lower_band": [],
            "forecast": [],
            "stats": {},
        }

    n = len(closes)
    x = list(range(n))
    slope, intercept = _linear_regression(x, closes)
    std = _sample_std(closes)
    trend_values = [intercept + slope * i for i in range(n)]

    trend_line = [{"time": t, "value": round(v, 4)} for t, v in zip(times, trend_values)]
    upper_band = [{"time": t, "value": round(v + STD_BANDS_K * std, 4)} for t, v in zip(times, trend_values)]
    lower_band = [{"time": t, "value": round(v - STD_BANDS_K * std, 4)} for t, v in zip(times, trend_values)]

    last_date = _parse_date(times[-1]) if times else None
    if not last_date:
        return {
            "trend_line": trend_line,
            "upper_band": upper_band,
            "lower_band": lower_band,
            "forecast": [],
            "stats": {"slope": slope, "intercept": intercept, "std": std, "last_date": None},
        }

    next_dates = _next_trading_days(last_date, FORECAST_DAYS)
    forecast = [
        {"time": d, "close": round(intercept + slope * (n + i), 4)}
        for i, d in enumerate(next_dates)
    ]

    logger.debug(
        "forecast computed n=%s slope=%.6f std=%.4f forecast_days=%s",
        n, slope, std, len(forecast),
    )
    return {
        "trend_line": trend_line,
        "upper_band": upper_band,
        "lower_band": lower_band,
        "forecast": forecast,
        "stats": {
            "slope": round(slope, 6),
            "intercept": round(intercept, 4),
            "std": round(std, 4),
            "last_date": times[-1],
        },
    }
