# Project Roadmap — Financial Assistant

This document analyses the codebase and outlines: (1) refactoring for production readiness, (2) areas to expand, (3) UI/UX improvements, and (4) new functionality with a short roadmap and research references.

---

## 1. Refactoring (rigid or not production-ready)

### 1.1 Configuration and secrets

- **Config (`backend/app/config.py`):** The code defines a `Settings(BaseSettings)` class with `env_file = ".env"`, but `get_settings()` bypasses Pydantic’s automatic env loading by passing `os.getenv(...)` explicitly into `Settings(...)`. That skips validation from the `.env` file; moreover, when running from `backend/`, Pydantic’s relative `env_file` is resolved from the current working directory, so a `.env` in the project root may not be found. Prefer calling `Settings()` with no arguments (so Pydantic loads and validates from env), or set `env_file` to an absolute path derived from the config file (e.g. `Path(__file__).resolve().parent.parent.parent / ".env"`).
- **`.env.example`:** Contains a real Alpha Vantage API key (`ALPHA_VANTAGE_API_KEY=KVVXM5EXLL6WJIEY`). Example files must use placeholders only (e.g. `your_alpha_vantage_key_here`). Rotate the exposed key and never commit real keys.
- **References:** [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/), [Twelve-Factor App Config](https://12factor.net/config).

### 1.2 CORS and main entry

- **`backend/main.py`:** CORS `allow_origins` is a long hardcoded list of localhost ports. For production, use env-driven origins (e.g. `CORS_ORIGINS`) or a single frontend URL; avoid maintaining a fixed list in code.

### 1.3 Scan service and adapters

- **Adapter registration:** `ScanService.__init__` instantiates a fixed list of adapters (`AlphaVantageAdapter()`, `YahooFinanceAdapter()`). To add or reorder adapters you must change code. Prefer registration via config or a registry (e.g. list of class names or factory functions from config).
- **Mock logic in scan_service:** `_mock_quote`, `_mock_series`, `_mock_fundamentals`, `_mock_news` and dev-mode branches are embedded in the same module as production logic. Consider a dedicated `MockAdapter` or a `dev_mode` adapter in the chain so the main flow stays clean.
- **Exception handling in adapters:** `_fetch_quote` / `_fetch_series` etc. use a bare `except Exception: continue`. At least log the exception (e.g. `logger.debug("adapter X failed: %s", e)`) so failures are visible in production.

### 1.4 Agent architecture

- **LangGraph not used:** `requirements.txt` includes `langgraph`, and docs refer to a “LangGraph agent”, but the advice pipeline is implemented as a sequential flow in the advice route (`backend/app/api/routes/advice.py`): scan → sub-agents → main agent. There is no `StateGraph`, no conditional edges, and no tool-calling loop. For production and future features (tools, branching, human-in-the-loop), consider implementing the pipeline as a LangGraph graph.
- **References:** [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/), [Multi-agent](https://langchain-ai.github.io/langgraph/concepts/multi_agent/).

### 1.5 Data model and cache

- **OHLCV table unused:** The schema defines an `ohlcv` table (and architecture/scan docs mention a TimescaleDB hypertable), but `ScanService` stores OHLCV series only in `scan_cache.payload` (e.g. `_get_ohlcv_cached` / `_set_ohlcv_cached` read/write `payload["series"]`). The `ohlcv` table is never written. Either use it (with a proper hypertable and range queries) for series storage and document it in scan.md, or remove the table/migration to avoid confusion.
- **References:** [TimescaleDB](https://www.timescale.com/), [scan.md](scan.md).

### 1.6 API and streaming

- **Chat / advice abort:** The frontend does not pass `AbortController`/`signal` to `fetch()` for the advice SSE (`GetAdviceButton`) or chat SSE (`sendChatMessage` in `lib/api.ts`). Users cannot cancel a long-running advice or chat request. Add abort support (e.g. pass `signal` to fetch and a “Stop” button that aborts) and, if needed, backend handling for client disconnect (e.g. close stream on connection drop).
- **Sessions API vs docs:** AGENTS.md mentions `POST /api/chat` (or `POST /api/sessions/{id}/messages`); the codebase implements only `POST /api/chat` (body: `session_id`, `message`). There is no `POST /api/sessions/{id}/messages`. Align AGENTS.md with implementation or add the session-scoped endpoint if desired.

### 1.7 Tests and quality

- **No automated tests:** There are no pytest (backend) or Jest/Vitest (frontend) tests in the repo. Only `data-testid` in `Sidebar.tsx` suggests future E2E. For production, add at least: (1) API route tests (e.g. FastAPI `TestClient`), (2) unit tests for scan_service, forecast_service, response_sanitizer, (3) frontend unit or E2E (e.g. Playwright) for critical flows.
- **References:** [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/), [Playwright](https://playwright.dev/).

---

## 2. Expansion (functionality still too small for production)

### 2.1 Authentication and authorization

- **Current state:** No auth. Any client can call all APIs and access all sessions.
- **Expand:** Add JWT (or session-based) auth: login/refresh endpoints, `Authorization` checks on protected routes, optional user-scoping of sessions (e.g. `user_id` on sessions). Document in architecture.md.
- **References:** [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/), [OAuth2 JWT](https://fastapi.tiangolo.com/advanced/oauth2-jwt/).

### 2.2 Rate limiting and validation

- **API rate limiting:** Only Alpha Vantage is rate-limited (in `rate_limiter.py`). There is no per-IP or per-user rate limiting on the FastAPI app. Add a middleware or dependency (e.g. slowapi or custom) to limit request rate per client.
- **Input validation:** `isin` in routes is a path/query string; consider Pydantic models and regex/format checks for ISIN and other inputs to avoid bad data and injection-style issues.

### 2.3 Observability and operations

- **Logging:** Backend uses `logging`; no structured fields (e.g. request_id, user_id). Consider structured logging (e.g. JSON) and correlation IDs for tracing advice and chat flows.
- **Health and readiness:** `GET /health` always returns 200 and does not check DB or dependencies. Add a readiness check (e.g. `GET /ready` or a query param on `/health`) that verifies DB connectivity (and optionally cache/LLM) so load balancers can stop sending traffic when the app is unhealthy.
- **Metrics:** No Prometheus/OpenMetrics or similar. For production, expose metrics (request count, latency, scan/advice duration, errors) to drive alerts and dashboards.

### 2.4 Scan and cache behaviour

- **Stale-while-revalidate:** scan.md describes it as optional; it is not implemented. Serving stale cache and refreshing in the background would improve perceived latency and reduce thundering herd on expiry.
- **Background scan:** Scan runs only on demand (advice or series/metrics). There is no queue (e.g. Celery, ARQ) or scheduled job to pre-warm or refresh cache for popular symbols. Optional expansion for production.

### 2.5 Deployment and DevOps

- **Docker Compose:** Does not run migrations on startup. README says “run migrations once after first start”. Add an init step or a dedicated job that runs `alembic upgrade head` so new deployments are consistent.
- **Frontend env in Docker:** `NEXT_PUBLIC_API_URL: http://localhost:8000` is wrong when the browser talks to the backend via a different host/port. Document or set this per environment (e.g. same-origin if behind a reverse proxy).

---

## 3. UI/UX (raw areas and improvements)

### 3.1 Structure and navigation

- **Single page:** The app is one page; stock and session selection are local state. Consider URL state (e.g. `/stock/[isin]`, `/session/[id]`) so users can bookmark, share, and refresh without losing context.
- **Header:** The main header shows “Stock: {selectedIsin}” (ISIN). Prefer “Stock: {name} ({symbol})” when available (data is in sidebar/list) so the header is human-readable.

### 3.2 Loading and empty states

- **Dashboard:** “Loading...” is plain text. Add skeleton placeholders for the chart and metrics grid so layout doesn’t jump and the app feels responsive.
- **Empty state:** When no stock is selected, the message is clear; when series/metrics fail, the same generic warning box is shown. Differentiate “no data yet” vs “error” and suggest actions (e.g. “Get financial advice” to trigger a scan, or “Try another symbol”).

### 3.3 Advice flow

- **Progress:** Progress bar and step list are good. Add a short “Searching for data and preparing analysis…” (or similar) when percent is 0 so users know the pipeline has started.
- **Errors:** If the advice pipeline fails, show a clear message and a “Retry” button instead of only setting `error` state.

### 3.4 Chat

- **Streaming:** Incoming tokens are appended; consider highlighting the streaming message or a subtle “Assistant is typing…” indicator.
- **Cancel:** No way to cancel a send. Add a “Stop” button that aborts the fetch and leaves the last partial reply (or a clear “Stopped” state).
- **Retry:** On network or server error, offer “Retry” for the last message.
- **Empty session:** When `sessionId` is null, the copy “Run ‘Get financial advice’ to open chat” is correct; keep it and ensure it’s visible when the chat panel is open but no advice has been run yet.

### 3.5 Sidebar and sessions

- **Past chats:** List is limited (e.g. 100 in API, 40px max-height in UI). Add “Load more” or pagination, and show date/time so users can find older sessions.
- **Stock dropdown:** Search and list work; consider virtualisation if the list grows very large (e.g. 10k+ rows) to keep scroll performant.

### 3.6 Accessibility and polish

- **Keyboard:** Ensure tab order and Enter/Space activate buttons; support Escape to close dropdowns.
- **Screen readers:** Use `aria-live` for progress and streaming advice/chat so updates are announced.
- **Focus:** After “Get financial advice” completes, move focus to the first line of the advice or to the chat input so keyboard users can continue without extra tabbing.

---

## 4. New functionality (roadmap and research)

### 4.1 Watchlists and alerts

- **Idea:** Let users save a list of favourite symbols (watchlist) and optionally set price/condition alerts (e.g. “Notify when AAPL &gt; 200”).
- **Realisation:** Backend: new table `watchlists` (user_id when auth exists, or anonymous id), `watchlist_items` (symbol/isin); optional `alerts` table (symbol, condition, threshold, notified_at). Frontend: “Add to watchlist” from dashboard/sidebar; a “Watchlist” panel; alerts can be implemented with a background job that evaluates conditions and sends in-app or email notifications.
- **References:** [Alpha Vantage Technical Indicators](https://www.alphavantage.co/documentation/) (for conditions), [IEX Cloud](https://iexcloud.io/docs/api/) (alternative real-time data).

### 4.2 Export and reporting

- **Idea:** Export advice and metrics (PDF or structured JSON/CSV) for a given stock or session.
- **Realisation:** Backend: endpoint `GET /api/stocks/{isin}/export?format=json|csv` and optionally `GET /api/sessions/{id}/export?format=pdf`. Use a library (e.g. WeasyPrint, reportlab, or a JS PDF lib in a worker) for PDF. Frontend: “Export” button on dashboard and/or session view.
- **References:** [WeasyPrint](https://weasyprint.org/), [reportlab](https://www.reportlab.com/).

### 4.3 Multi-symbol comparison

- **Idea:** Compare metrics and performance of 2–5 symbols in one view (e.g. side-by-side charts, common KPIs).
- **Realisation:** Backend: re-use existing `get_series` and `get_metrics` per symbol; optional endpoint `GET /api/compare?isins=A,B,C` that returns aggregated series and metrics. Frontend: “Compare” mode: select multiple symbols, show multiple lines on one chart and a comparison metrics table. Existing adapters and scan service already support multiple symbols.
- **References:** [Alpha Vantage Batch Quotes](https://www.alphavantage.co/documentation/#batch-quotes) (if you need many quotes in one call).

### 4.4 More data sources

- **Ideas:** Integrate fundamentals or news from Simfin, SEC Edgar, FRED, or Stooq to diversify and reduce dependency on a single provider.
- **Realisation:** Implement new adapters (e.g. `SimfinAdapter`, `FredAdapter`) per `DataSourceAdapter` in `backend/app/adapters/`, register them in the scan service (or via config), and document in architecture.md and scan.md. Optionally create a `research.md` for data source URLs and API notes.
- **References:** [Simfin](https://simfin.com/), [SEC Edgar](https://www.sec.gov/edgar), [FRED API](https://fred.stlouisfed.org/docs/api/fred/), [Pandas Datareader](https://pandas-datareader.readthedocs.io/) (Stooq, etc.).

### 4.5 LangGraph agent with tools

- **Idea:** Turn the current linear pipeline into a LangGraph agent that can decide when to fetch data, call tools (get_quote, get_series, get_news, search_web), and when to synthesize advice. Enables multi-turn reasoning and optional human-in-the-loop.
- **Realisation:** Define a state schema (e.g. messages, scan_context, summaries, current_step); add nodes for “orchestrator”, “scan”, “sub_agents”, “main_agent”; add tools that call ScanService and web_search; use conditional edges from orchestrator to scan/tools/synthesis. Expose the same advice SSE from the graph’s stream. Keep sub-agents as internal steps or as tool-calling subgraphs.
- **References:** [LangGraph](https://langchain-ai.github.io/langgraph/), [LangGraph Tools](https://langchain-ai.github.io/langgraph/how-tos/tool-calling/), [MCP](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#mcp).

### 4.6 Suggested priority order

| Priority | Item                         | Effort | Impact |
|----------|------------------------------|--------|--------|
| 1        | Remove API key from .env.example, fix config loading | Low    | Security / correctness |
| 2        | Add API and service tests   | Medium | Stability |
| 3        | Auth (JWT) + user-scoped sessions | High   | Production |
| 4        | UI: URL state, skeletons, abort/retry for streams | Medium | UX |
| 5        | Use or drop OHLCV table; document cache strategy | Low    | Clarity |
| 6        | Stale-while-revalidate for scan | Medium | Latency |
| 7        | Watchlists; optional alerts | Medium | Engagement |
| 8        | LangGraph agent with tools  | High   | Flexibility and features |
| 9        | Export (JSON/CSV/PDF)       | Medium | Usefulness |
| 10       | Multi-symbol comparison     | Medium | Differentiation |

---

## References (consolidated)

- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [LangChain ChatGroq](https://python.langchain.com/docs/integrations/chat/groq/)
- [LangGraph concepts](https://langchain-ai.github.io/langgraph/concepts/)
- [TimescaleDB](https://www.timescale.com/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [NewsData.io](https://newsdata.io/documentation) (financial news)
- [architecture.md](architecture.md), [scan.md](scan.md), [AGENTS.md](AGENTS.md) — project docs; optionally add `research.md` for data source URLs and API notes.