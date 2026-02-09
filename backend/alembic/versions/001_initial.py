"""Initial schema: symbol_resolution, scan_cache, ohlcv, sessions, messages.

Revision ID: 001
Revises:
Create Date: 2025-02-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "symbol_resolution",
        sa.Column("isin", sa.String(20), primary_key=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "scan_cache",
        sa.Column("symbol", sa.String(20), primary_key=True),
        sa.Column("data_type", sa.String(50), primary_key=True),
        sa.Column("interval", sa.String(20), primary_key=True, server_default=""),
        sa.Column("payload", sa.dialects.postgresql.JSONB(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_scan_cache_symbol_data_type", "scan_cache", ["symbol", "data_type"], unique=False)

    op.create_table(
        "ohlcv",
        sa.Column("time", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("symbol", sa.String(20), primary_key=True),
        sa.Column("open", sa.Numeric(20, 4), nullable=True),
        sa.Column("high", sa.Numeric(20, 4), nullable=True),
        sa.Column("low", sa.Numeric(20, 4), nullable=True),
        sa.Column("close", sa.Numeric(20, 4), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
    )
    # Optional: enable TimescaleDB and convert to hypertable in a separate migration if available

    op.create_table(
        "sessions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("isin", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scan_context", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("sub_agent_summaries", sa.dialects.postgresql.JSONB(), nullable=True),
    )
    op.create_table(
        "messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("session_id", sa.BigInteger(), sa.ForeignKey("sessions.id"), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("sessions")
    op.drop_table("ohlcv")
    op.drop_index("ix_scan_cache_symbol_data_type", table_name="scan_cache")
    op.drop_table("scan_cache")
    op.drop_table("symbol_resolution")
