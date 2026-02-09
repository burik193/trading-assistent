import os
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env from project root so DATABASE_URL is set
try:
    from dotenv import load_dotenv
    backend_dir = Path(__file__).resolve().parent.parent
    # Try project root (parent of backend) and cwd parent
    load_dotenv(backend_dir.parent / ".env")
    load_dotenv(Path.cwd().parent / ".env")
except ImportError:
    pass

from app.db.session import Base
from app.models.base import SymbolResolution, ScanCache, OHLCV, Session, Message

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/analyse_stocks")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        connection = connectable.connect()
    except UnicodeDecodeError:
        raise RuntimeError(
            "Database connection failed. The server may have sent a non-UTF-8 error (e.g. wrong password). "
            "Check DATABASE_URL in .env and your PostgreSQL password. "
            "On Windows, you can set PostgreSQL lc_messages to en_US.UTF-8 to avoid this."
        ) from None
    with connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
