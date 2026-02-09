"""FastAPI app entry point."""
import logging
import os
import sys
from pathlib import Path

# Ensure app is on path when running as python main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Logging: app loggers to stdout so uvicorn/console show scan and advice steps/errors
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logging.getLogger("app").setLevel(logging.DEBUG)

# Load .env from project root (try two common locations)
try:
    from dotenv import load_dotenv
    _root = Path(__file__).resolve().parent.parent
    load_dotenv(_root / ".env")
    load_dotenv(Path.cwd().parent / ".env")
except ImportError:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import stocks, advice, chat, sessions
from app.config import get_settings

logger = logging.getLogger("app")

app = FastAPI(title="Financial Assistant API", version="0.1.0")


@app.on_event("startup")
def log_startup_mode():
    settings = get_settings()
    if settings.dev_mode:
        logger.warning("Backend started in DEV mode — mocks only, no Alpha Vantage / Yahoo / GROQ calls.")
    else:
        logger.info("Backend started in NORMAL mode — real APIs and LLM.")


@app.exception_handler(Exception)
async def global_exception_handler(_request: Request, exc: Exception):
    """Return a generic error so we never expose stack traces or provider messages."""
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )

# Allow frontend on common localhost ports (dev: 3000–3010; proxy avoids CORS when using same-origin)
_cors_origins = [
    "http://localhost:3000", "http://127.0.0.1:3000",
    "http://localhost:3001", "http://127.0.0.1:3001",
    "http://localhost:3002", "http://127.0.0.1:3002",
    "http://localhost:3003", "http://127.0.0.1:3003",
    "http://localhost:3004", "http://127.0.0.1:3004",
    "http://localhost:3005", "http://127.0.0.1:3005",
    "http://localhost:3006", "http://127.0.0.1:3006",
    "http://localhost:3007", "http://127.0.0.1:3007",
    "http://localhost:3008", "http://127.0.0.1:3008",
    "http://localhost:3009", "http://127.0.0.1:3009",
    "http://localhost:3010", "http://127.0.0.1:3010",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stocks.router, prefix="/api", tags=["stocks"])
app.include_router(advice.router, prefix="/api", tags=["advice"])
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(sessions.router, prefix="/api", tags=["sessions"])


@app.get("/health")
def health():
    return {"status": "ok"}
