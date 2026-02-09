# Financial Assistant — Architecture

## Overview and goals

The application is a **chat-based financial assistant** that:

- Lets users pick a stock from a sidebar dropdown (populated from `stocks_list.csv`).
- Shows a **performance graph** with selectable timescales (1D, 5D, 1M, 3M, 1Y, etc.) and a **metrics panel** (fundamentals + technicals).
- Provides an **AI assistant** that answers questions using cached stock data and optional web search (e.g. latest news).
- **Scans** external data (Alpha Vantage, Yahoo Finance, etc.) on demand and **caches** it in the database so the agent always has context and API rate limits are respected.

Architecture is **extendable**: new data sources are added via adapters behind a unified interface; the agent and API contract stay unchanged.

---

## Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React or Next.js, dark theme (Tailwind), chat UI + sidebar, performance graph, metrics panel. Streaming for chat (SSE or WebSocket). |
| **Backend** | Python, FastAPI, LangChain, LangGraph, GROQ (qwen3-32b). REST API + agent + scan service + data adapters. |
| **Database** | PostgreSQL with TimescaleDB extension: app data, symbol resolution, scan cache, OHLCV time series, chat history. |
| **External** | Alpha Vantage (MCP or direct API), Yahoo Finance (yfinance / search API). |

---

## High-level diagram

```mermaid
flowchart LR
  subgraph frontend [Frontend]
    UI[Chat UI]
    Sidebar[Sidebar + Stock Dropdown]
    Graph[Performance Graph]
    Metrics[Metrics Panel]
  end

  subgraph backend [Backend]
    API[FastAPI API]
    Agent[LangGraph Agent]
    Scan[Scan Service]
    Adapters[Data Adapters]
  end

  subgraph data [Data]
    PG[(PostgreSQL + TimescaleDB)]
  end

  subgraph external [External]
    AV[Alpha Vantage MCP/API]
    YF[Yahoo Finance]
  end

  UI --> API
  Sidebar --> API
  Graph --> API
  API --> Agent
  API --> Scan
  Agent --> Scan
  Scan --> Adapters
  Adapters --> AV
  Adapters --> YF
  Scan --> PG
  Agent --> PG
```

---

## Backend layout

### API layer

REST endpoints (examples):

- `POST /api/chat` — send message, get assistant reply (streaming optional).
- `GET /api/stocks` — list stocks (from CSV or DB).
- `GET /api/stocks/{id}/series` — OHLCV series for graph (query params: interval, from, to).
- `GET /api/stocks/{id}/metrics` — fundamentals + technicals.
- `POST /api/stocks/{id}/scan` — trigger scan and return/cache data.

Auth can be added later (e.g. JWT) without changing this layout.

### Agent (LangGraph)

- **Orchestrator** node: routes user questions and decides which tools to call.
- **Tools** (subagents): e.g. `get_stock_data` (calls Scan), `get_metrics`, `get_news`, `search_web` (optional).
- Tools read from **cache first** via the Scan service; Scan fills cache from adapters when data is missing or TTL-expired.
- LLM: GROQ with `qwen3-32b` via LangChain `ChatGroq`; env `GROQ_API_KEY`.

### Scan service

- **Input:** symbol (or ISIN; then resolve to symbol via DB or Yahoo).
- **Steps:** (1) Resolve ISIN → ticker if needed. (2) For each required data type (quote, series, fundamentals, news), check cache. (3) If miss or TTL expired, call adapters (respecting rate limits), write to DB. (4) Return aggregated context for the agent.
- See [scan.md](scan.md) for TTLs, cache keys, and batching.

### Data adapters (unified interface)

All external sources are accessed through a **DataSourceAdapter**-style interface so new sources are plug-in.

**Abstract interface (conceptual):**

- `get_quote(symbol) -> dict`
- `get_series(symbol, interval) -> list[OHLCV]` (interval: 1d, 1w, 1m, etc.)
- `get_fundamentals(symbol) -> dict` (overview, income, balance, etc.)
- `get_news(symbol, limit) -> list[Article]`

**Current adapters:**

- **AlphaVantageAdapter** — TIME_SERIES_*, COMPANY_OVERVIEW, NEWS_SENTIMENT, INCOME_STATEMENT, etc. (MCP or direct REST).
- **YahooFinanceAdapter** — quote, history, news; used for ISIN→ticker resolution and as fallback.

New source = new adapter implementing the same interface + registration in the Scan service; no change to agent or API.

### Suggested folder structure

```
backend/
  app/
    api/           # FastAPI routes
    agent/         # LangGraph graph, nodes, tools
    services/      # scan_service, etc.
    adapters/      # data_source.py (interface), alpha_vantage.py, yahoo.py
    models/        # DB models (SQLAlchemy or similar)
    db/            # connection, migrations
  Dockerfile
  requirements.txt
```

---

## Data model (conceptual)

| Table / structure | Purpose |
|-------------------|--------|
| **symbol_resolution** | isin, symbol, name, source, updated_at. Cache ISIN → ticker (and name). |
| **scan_cache** | symbol, data_type, interval (nullable), payload (JSONB or ref), fetched_at. TTL per data_type (see scan.md). |
| **ohlcv** (hypertable) | time, symbol, open, high, low, close, volume. TimescaleDB hypertable for fast range queries and compression. |
| **chats** | session_id, user_id (optional), created_at. |
| **messages** | chat_id, role (user/assistant), content, created_at. |

Primary key for `scan_cache`: `(symbol, data_type, interval)` so we can upsert on refresh.

---

## Docker

### Compose services

- **backend** — FastAPI + uvicorn (Python 3.11+). Depends on `postgres`. Env: `DATABASE_URL`, `GROQ_API_KEY`, `ALPHA_VANTAGE_API_KEY` (if using direct API).
- **frontend** — Node build → static assets; serve with Nginx, or dev server in development. Proxies `/api` to backend if using Nginx.
- **postgres** — PostgreSQL with TimescaleDB extension. Volume for data; init script to enable extension and create schema if needed.

Optional: **nginx** as reverse proxy in front of frontend + backend (e.g. `/api` → backend, `/` → frontend).

### Environment

`.env.example`:

- `GROQ_API_KEY` — required for LLM.
- `DATABASE_URL` — e.g. `postgresql://user:pass@postgres:5432/dbname`.
- `ALPHA_VANTAGE_API_KEY` — if using Alpha Vantage REST directly (optional if using MCP with key in MCP config).

### Images

- **backend/Dockerfile:** Python base, install dependencies, run uvicorn.
- **frontend/Dockerfile:** Node build, copy dist to Nginx image or run dev server.

---

## Security and scaling notes

- **Secrets:** All API keys and DB URL from environment; never in code or repo.
- **Rate limits:** Alpha Vantage free tier (25/day, 5/min) is respected by Scan service (cache-first, batch per symbol). See scan.md.
- **Auth:** Not in initial scope; add JWT or session-based auth later; API layer is the single place to enforce it.
- **Scaling:** Backend can run multiple workers behind a load balancer; DB is single source of truth. For high throughput, consider read replicas and queue-based scan jobs later.

---

## Research references

- [Alpha Vantage API Documentation](https://www.alphavantage.co/documentation/) — time series, fundamentals, news.
- [LangChain ChatGroq (GROQ integration)](https://python.langchain.com/docs/integrations/chat/groq/) — LLM integration.
- [LangGraph concepts (multi-agent, MCP)](https://langchain-ai.github.io/langgraph/concepts/multi_agent/) — agent and MCP usage.
- [TimescaleDB](https://www.timescale.com/) — PostgreSQL extension for time-series (OHLCV).
- [investiny](https://pypi.org/project/investiny/) — interim replacement for investpy (Investing.com).
- [research.md](research.md) — project-specific list of free financial data sources.
