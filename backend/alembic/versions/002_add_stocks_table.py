"""Add stocks table and seed from CSV.

Revision ID: 002
Revises: 001
Create Date: 2025-02-04

"""
from pathlib import Path
import csv
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stocks",
        sa.Column("isin", sa.String(20), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
    )
    # Seed from stocks_list.csv (project root)
    # Migration file is in backend/alembic/versions/ -> project root is ../../../..
    migration_dir = Path(__file__).resolve().parent
    project_root = migration_dir.parent.parent.parent
    csv_path = project_root / "stocks_list.csv"
    if csv_path.exists():
        conn = op.get_bind()
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                isin = (row.get("ISIN") or "").strip()
                name = (row.get("Name") or "").strip()
                if isin:
                    conn.execute(
                        text("INSERT INTO stocks (isin, name) VALUES (:isin, :name) ON CONFLICT (isin) DO NOTHING"),
                        {"isin": isin, "name": name},
                    )


def downgrade() -> None:
    op.drop_table("stocks")
