"""Quick check: list tables and stocks count."""
import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")
except ImportError:
    pass
from sqlalchemy import create_engine, text
url = os.getenv("DATABASE_URL", "")
if not url:
    print("DATABASE_URL not set")
    exit(1)
e = create_engine(url)
with e.connect() as c:
    r = c.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY 1"))
    tables = [row[0] for row in r]
    print("Tables:", tables)
    if "stocks" in tables:
        r2 = c.execute(text("SELECT COUNT(*) FROM stocks"))
        print("Stocks count:", r2.scalar())
