"""Create database analyse_stocks if it does not exist. Run once; DATABASE_URL from .env."""
import os
import sys
from pathlib import Path

# Load .env from project root
try:
    from dotenv import load_dotenv
    backend_dir = Path(__file__).resolve().parent.parent
    load_dotenv(backend_dir.parent / ".env")
    load_dotenv(Path.cwd().parent / ".env")
except ImportError:
    pass

url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")
# If URL already has analyse_stocks, connect to postgres to create it
base_url = url.replace("/analyse_stocks", "/postgres") if "/analyse_stocks" in url else url

try:
    from sqlalchemy import create_engine, text
    engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
    with engine.connect() as conn:
        row = conn.execute(text("SELECT 1 FROM pg_database WHERE datname = 'analyse_stocks'")).fetchone()
        if not row:
            conn.execute(text("CREATE DATABASE analyse_stocks"))
            print("Created database analyse_stocks")
        else:
            print("Database analyse_stocks already exists")
except UnicodeDecodeError as e:
    print("Database connection failed. The server may have sent a non-UTF-8 error (e.g. wrong password). Check DATABASE_URL in .env and your PostgreSQL password.", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print("Error:", e, file=sys.stderr)
    sys.exit(1)
