"""Stocks API: list, series, metrics, forecast."""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db

logger = logging.getLogger(__name__)
from app.models.base import Stock, SymbolResolution
from app.services.forecast_service import compute_forecast
from app.services.response_sanitizer import (
    DATA_UNAVAILABLE_MESSAGE,
    is_safe_metrics,
    is_safe_series,
)
from app.services.scan_service import ScanService

router = APIRouter()


@router.get("/stocks")
def list_stocks(db: Session = Depends(get_db)):
    """List stocks from Postgres with optional resolved symbol from symbol_resolution."""
    stocks = db.query(Stock).order_by(Stock.name).all()
    resolutions = {r.isin: r for r in db.query(SymbolResolution).all()}
    return [
        {
            "isin": s.isin,
            "name": s.name,
            "symbol": resolutions[s.isin].symbol if s.isin in resolutions else None,
        }
        for s in stocks
    ]


@router.get("/stocks/{isin}/series")
def get_series(
    isin: str,
    interval: str = "1d",
    include_forecast: bool = False,
    db: Session = Depends(get_db),
):
    """OHLCV series for graph. interval: 1d, 1w, 1m. include_forecast=true adds trend, std bands, next 3 days prognosis."""
    scan = ScanService(db)
    series = scan.get_series(isin, interval)
    if series is None:
        symbol = scan.resolve_isin(isin) if not (isin.isupper() and len(isin) <= 6 and " " not in isin) else isin
        detail = "Symbol not resolved for this ISIN" if not symbol else DATA_UNAVAILABLE_MESSAGE
        raise HTTPException(status_code=404, detail=detail)
    if not is_safe_series(series):
        raise HTTPException(status_code=404, detail=DATA_UNAVAILABLE_MESSAGE)
    out: dict = {"series": series}
    if include_forecast and interval == "1d" and len(series) >= 2:
        forecast_data = compute_forecast(series)
        out["forecast"] = forecast_data.get("forecast", [])
        out["trend_line"] = forecast_data.get("trend_line", [])
        out["upper_band"] = forecast_data.get("upper_band", [])
        out["lower_band"] = forecast_data.get("lower_band", [])
        out["forecast_stats"] = forecast_data.get("stats", {})
    return out


@router.get("/stocks/{isin}/metrics")
def get_metrics(
    isin: str,
    db: Session = Depends(get_db),
):
    """Fundamentals/metrics for metrics panel. Returns 200 with {} when no metrics (e.g. ETF) so dashboard still works."""
    scan = ScanService(db)
    metrics = scan.get_metrics(isin)
    if metrics is None:
        symbol = scan.resolve_isin(isin) if not (isin.isupper() and len(isin) <= 6 and " " not in isin) else isin
        logger.info("metrics missing for isin=%s symbol=%s (no fundamentals from adapters)", isin, symbol)
        return {}
    if not is_safe_metrics(metrics):
        logger.info("metrics unsafe for isin=%s (blocker content); returning empty", isin)
        return {}
    return metrics
