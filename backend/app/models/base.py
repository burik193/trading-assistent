"""SQLAlchemy models for symbol_resolution, scan_cache, ohlcv, sessions, messages."""
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    BigInteger,
    DateTime,
    Numeric,
    ForeignKey,
    Text,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.session import Base


class Stock(Base):
    """Stock list (ISIN + name), seeded from stocks_list.csv."""
    __tablename__ = "stocks"

    isin = Column(String(20), primary_key=True)
    name = Column(String(255), nullable=False)


class SymbolResolution(Base):
    """ISIN -> ticker resolution cache."""
    __tablename__ = "symbol_resolution"

    isin = Column(String(20), primary_key=True)
    symbol = Column(String(20), nullable=False)
    name = Column(String(255), nullable=True)
    source = Column(String(50), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ScanCache(Base):
    """Cached non-time-series data: quote, fundamentals, news."""
    __tablename__ = "scan_cache"

    symbol = Column(String(20), primary_key=True)
    data_type = Column(String(50), primary_key=True)
    interval = Column(String(20), primary_key=True, default="")
    payload = Column(JSONB, nullable=False)
    fetched_at = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (Index("ix_scan_cache_symbol_data_type", "symbol", "data_type"),)


class OHLCV(Base):
    """OHLCV time series (TimescaleDB hypertable)."""
    __tablename__ = "ohlcv"

    time = Column(DateTime(timezone=True), primary_key=True)
    symbol = Column(String(20), primary_key=True)
    open = Column(Numeric(20, 4), nullable=True)
    high = Column(Numeric(20, 4), nullable=True)
    low = Column(Numeric(20, 4), nullable=True)
    close = Column(Numeric(20, 4), nullable=True)
    volume = Column(BigInteger, nullable=True)


class Session(Base):
    """One chat/session per stock (one advice run + follow-up messages)."""
    __tablename__ = "sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    isin = Column(String(20), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    scan_context = Column(JSONB, nullable=True)
    sub_agent_summaries = Column(JSONB, nullable=True)

    messages = relationship("Message", back_populates="session", order_by="Message.created_at")


class Message(Base):
    """Chat message in a session."""
    __tablename__ = "messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("Session", back_populates="messages")
