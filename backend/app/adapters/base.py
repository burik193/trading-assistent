"""Unified data source adapter interface."""
from abc import ABC, abstractmethod
from typing import Any, Optional


class DataSourceAdapter(ABC):
    """Abstract interface for external financial data sources."""

    @abstractmethod
    def get_quote(self, symbol: str) -> Optional[dict[str, Any]]:
        """Latest price and volume for symbol. Returns None if unsupported or error."""
        pass

    @abstractmethod
    def get_series(
        self,
        symbol: str,
        data_type: str,
    ) -> Optional[list[dict[str, Any]]]:
        """OHLCV series. data_type: daily, weekly, monthly. Returns list of {time, open, high, low, close, volume}."""
        pass

    @abstractmethod
    def get_fundamentals(self, symbol: str) -> Optional[dict[str, Any]]:
        """Company overview, income, balance, cash flow, earnings. Returns dict or None."""
        pass

    @abstractmethod
    def get_news(self, symbol: str, limit: int = 10) -> Optional[list[dict[str, Any]]]:
        """News/sentiment for symbol. Returns list of articles or None."""
        pass

    def resolve_isin(self, isin: str) -> Optional[dict[str, Any]]:
        """Resolve ISIN to ticker and name. Returns {symbol, name} or None. Optional override."""
        return None

    def resolve_by_name(self, name: str) -> Optional[dict[str, Any]]:
        """Resolve stock name to ticker and name. Returns {symbol, name} or None. Optional override."""
        return None
