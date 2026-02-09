# AGENTS.md — Operating manual for AI agents and developers

## What this project is

A **chat-based financial assistant**: users select a stock from a sidebar (from `stocks_list.csv`), see a **dashboard** (graphs and colored metrics only; no LLM), then click **"Get financial advice"** to run a search pipeline. The pipeline: scan external data (Alpha Vantage, Yahoo), run **sub-agents** per step and for mathematical context, then a **main agent** synthesizes advice and streams it. Afterwards **chat** opens; the agent has full session context (scan, sub-agent summaries, history). **One stock per session**; sessions are stored as chats. New stock = new session.

- **Architecture:** [architecture.md](architecture.md) — stack, data flow, backend layout.
- **Scan and cache:** [scan.md](scan.md) — TTLs, cache keys, rate limits.

---

## High-level flow

1. User selects stock (ISIN/Name) → **dashboard** loads: graphs (`GET /api/stocks/{isin}/series`), metrics (`GET /api/stocks/{isin}/metrics`). No advice yet.
2. User clicks **"Get financial advice"** → `POST /api/stocks/{isin}/advice` runs: scan (with progress events), sub-agents per step + math sub-agent, main agent. Frontend shows loading bar (%), status bar (steps, current, failures). Main agent reply streamed via SSE.
3. **Chat** opens; user can ask follow-up questions. `POST /api/chat` (or `POST /api/sessions/{id}/messages`) with session context (stock, scan, sub-agent summaries, history). Session saved as one chat in sidebar.
4. New stock → new session (new chat).

---

## Where to find things

| To change … | Look here |
|-------------|-----------|
| API routes | `backend/app/api/routes/` |
| Agent graph and tools | `backend/app/agent/` |
| Scan logic and TTLs | `backend/app/services/scan_service.py`, [scan.md](scan.md) |
| Adapters | `backend/app/adapters/` (base: `base.py`) |
| DB models | `backend/app/models/` |
| Rate limiter | `backend/app/services/rate_limiter.py` |
| Frontend pages and layout | `frontend/app/` |
| Frontend components | `frontend/components/` |
| Docker | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` |

---

## Advice pipeline and sessions

- **Scan:** Produces quote, daily/weekly/monthly, fundamentals, news per scan.md. Each logical step (e.g. "Fetching price data", "Fetching news") is reported to frontend (progress events).
- **Sub-agents:** Each step's context goes to a dedicated sub-agent (e.g. news → news sub-agent). Mathematical context (series, metrics, stats) goes to a dedicated math/analysis sub-agent. Sub-agents return short summaries (behavior, analysis, buy/short view, outlook).
- **Main agent:** Receives all sub-agent summaries; synthesizes final financial advice; streamed via SSE.
- **Session:** Created/updated on advice run. Stores: isin, title (e.g. "{Stock name} – {date}"), scan_context (JSONB), sub_agent_summaries (JSONB), messages. Chat endpoint loads session context for follow-up replies.

---

## Chat and web search

- **Chat** (`POST /api/chat`): Always receives prior analysis (sub_agent_summaries, scan_context) and conversation history. If the user's question cannot be answered from that context (e.g. "What caused the decline?"), the model is asked to output **SEARCH_QUERIES: q1 | q2**; the backend then runs a **web search** and passes the snippets back to the model with the same analysis. The model always bases its answer on our analysis first and supplements with web results when needed.
- **Web search** (`backend/app/services/web_search.py`): Three-tier flow — (1) **Structured financial news API** (NewsData.io Latest API, https://newsdata.io/documentation) when `FINANCIAL_NEWS_API_KEY` is set and a symbol is available (ticker-specific articles); (2) **RSS feeds** (e.g. Google News RSS) for each query; (3) **DuckDuckGo news** fallback (`duckduckgo-search`). **Suggested search terms** come from: symbol, stock name/sector (and a static commodity list as fallback), plus **dynamic keywords** from the **keywords sub-agent** (`backend/app/agent/sub_agents.py`: `run_keywords_sub_agent`) — an LLM that derives 5–10 search terms per stock (commodities, sector, themes) from fundamentals/context.

---

## How to add a new data source

1. Implement `DataSourceAdapter` in `backend/app/adapters/<name>.py` (see `base.py`).
2. Register adapter in scan service (e.g. list of adapters; try primary then fallbacks).
3. Document in architecture.md "Current adapters" and in scan.md if new data_type or TTL.
4. No change to API or agent tools unless you intentionally expose new data.

---

## How to add a new agent tool

1. Add function in `backend/app/agent/tools.py` that takes symbol/ISIN or query; call scan_service or adapters.
2. Register tool with LLM in graph.
3. Update agent state/types if needed. Do not call external APIs directly from tools.

---

## Conventions

- API uses **ISIN** for stocks. Backend resolves to symbol via `symbol_resolution`.
- All external data via Scan + adapters. Secrets from env. TTLs and rate limits per scan.md.
- Backend: type hints, FastAPI. Frontend: TypeScript, dark theme.
- **Logging:** Always add logging for new features, in both frontend and backend. Non-negotiable. Backend: use `logging.getLogger(__name__)`; frontend: use `console.log` or a structured logger. See `.cursor/rules/non-negotiable.mdc`.

---

## What not to do

- Do not hardcode API keys.
- Do not bypass Scan service for Alpha Vantage or Yahoo.
- Do not change cache key design (symbol, data_type, interval) without updating scan.md and scan_service.
- Do not remove or rename adapter interface methods without updating all adapters and scan_service.

---

## Running the project

- **Full stack:** `docker-compose up` (after Phase 4).
- **Backend only:** From `backend/`: `uvicorn app.main:app --reload`. Requires PostgreSQL with TimescaleDB and `.env` (copy from `.env.example`).
- **Frontend only:** From `frontend/`: `npm run dev`. Set `NEXT_PUBLIC_API_URL` to backend URL.
