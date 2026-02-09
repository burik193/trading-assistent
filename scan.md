# Scan and cache strategy

This document describes how the financial assistant **scans** external data (Alpha Vantage, Yahoo Finance, etc.) and **caches** it so the agent has up-to-date context while respecting API rate limits.

---

## When scan runs

- **On “select stock”** — when the user picks a stock from the sidebar dropdown, the frontend can request data for that symbol (or ISIN). The backend runs a scan if needed.
- **On first message about a symbol** — when the user asks a question that refers to a stock (e.g. “What’s the latest on IBM?”), the agent (via tools) calls the Scan service. Scan loads from cache or fetches and caches.
- **On explicit “Refresh”** — the user can trigger a refresh for the current stock; Scan re-fetches and updates cache (subject to TTL / rate limits).

Scan is **automatic** in the sense that any request for a stock triggers a cache lookup and, on miss or expiry, a fetch. No separate “scheduled” scan is required for the basic flow.

---

## Data types and TTLs

| Data type | Description | TTL | Notes |
|-----------|-------------|-----|--------|
| **quote** | Latest price, volume | 15 min | Realtime-like; short TTL. |
| **daily** | Daily OHLCV series (≥1 year when available) | 7 d | TIME_SERIES_DAILY (full); Yahoo 2y. |
| **weekly** | Weekly OHLCV | 7 d | TIME_SERIES_WEEKLY. |
| **monthly** | Monthly OHLCV | 7 d | TIME_SERIES_MONTHLY. |
| **fundamentals** | Company overview, income, balance, cash flow, earnings | 7 d | COMPANY_OVERVIEW, INCOME_STATEMENT, etc. |
| **news** | News and sentiment | 1 h | NEWS_SENTIMENT. |
| **ISIN resolution** | ISIN → ticker (and name) | 30 d | Long-lived or permanent; rarely changes. |

Cache is considered **stale** when `now - fetched_at > TTL`. On next request, Scan re-fetches and overwrites (or upserts) the cache row.

---

## Cache key design

Cache key is **`(symbol, data_type, interval)`**:

- **symbol** — resolved ticker (e.g. `IBM`). For ISIN resolution we use a separate table keyed by ISIN.
- **data_type** — one of: `quote`, `daily`, `weekly`, `monthly`, `fundamentals`, `news`.
- **interval** — optional; used only when the same data_type has multiple intervals (e.g. for future extensions). For OHLCV we use data_type = daily/weekly/monthly instead of interval.

Examples:

- `(IBM, quote, null)`
- `(IBM, daily, null)`
- `(IBM, fundamentals, null)`
- `(IBM, news, null)`

---

## Scan flow

1. **Resolve identifier to symbol**
   - If input is ISIN: look up `symbol_resolution` by ISIN. If missing, try adapters: (1) Yahoo Finance search by ISIN, (2) if that fails, load stock name from `stocks` and try Yahoo search by name or Alpha Vantage SYMBOL_SEARCH by name; then insert/update `symbol_resolution` and use the resolved symbol.
   - If input is already a symbol (ticker), use it.

2. **For each required data type** (quote, daily, fundamentals, news, etc.):
   - **Check cache:** select from `scan_cache` (or OHLCV hypertable for series) where `symbol = X` and `data_type = Y` and `interval = Z` and `fetched_at` within TTL.
   - **If hit:** use cached payload; skip external call.
   - **If miss or expired:** call the appropriate adapter (Alpha Vantage or Yahoo), **respecting rate limits** (see below), then **write** to DB (upsert `scan_cache` or insert into `ohlcv`), set `fetched_at = now()`.

3. **Return** aggregated context (e.g. quote + series + fundamentals + news) to the caller (agent or API).

Optional: **stale-while-revalidate** — serve stale cache immediately and trigger a background refresh so the next request gets fresh data. Can be added later without changing the core flow.

---

## Structured analytics payload

All fetched data follows a **canonical schema** so the dashboard, mathematical analytics (returns, volatility, moving averages), and the agent can rely on a fixed shape. Scan context and `GET /api/stocks/{isin}/series` and `/metrics` use this schema; agent and math code should consume it as-is.

- **OHLCV series:** Array of objects `{ time, open, high, low, close, volume }`.  
  - `time`: string `YYYY-MM-DD`.  
  - `open`, `high`, `low`, `close`: number or null.  
  - `volume`: integer or null.  
  - Sorted ascending by `time`.

- **Quote:** Object `{ symbol, price, volume, change, change_percent }` (all optional; types as returned by adapters).

- **Fundamentals:** Flat dict (e.g. `Symbol`, `Name`, `MarketCapitalization`, `PERatio`, `EPS`, `52WeekHigh`, `52WeekLow`, `Beta`; plus ETF_PROFILE fields when available).

- **News:** Array of objects `{ title, url, summary, time_published, sentiment_score? }` (sentiment_score optional).

---

## Alpha Vantage rate limits and batching

- **Free tier:** 25 requests per day, 5 requests per minute.
- **Strategy:**
  - **Cache-first:** Always check DB before calling Alpha Vantage. One successful fetch per (symbol, data_type) per TTL window avoids redundant calls.
  - **Batch per symbol:** On first request for a symbol, we may need several calls (quote, daily, fundamentals, news). Space them out (e.g. 1 call every 12+ seconds to stay under 5/min). Alternatively, prioritize: fetch quote + daily + fundamentals in one “full” scan, then news in a follow-up or next request.
  - **Daily budget:** With 25/day, we can fully refresh ~6 symbols per day (4 calls each: quote, daily, fundamentals, news) if we use only Alpha Vantage. Use **Yahoo as fallback** for quote/series when Alpha Vantage budget is exhausted or for ISIN resolution.
  - **Queue/delay:** If multiple symbols are requested in a short time, queue Alpha Vantage calls and add delays (e.g. 12 s between calls) to avoid 429.

---

## Yahoo Finance usage

- **ISIN → ticker:** Use Yahoo Finance search API (e.g. `https://query1.finance.yahoo.com/v1/finance/search?q=<ISIN>`) with proper headers; parse result for ticker. Cache in `symbol_resolution`.
- **Fallback:** When Alpha Vantage is rate-limited or for symbols where Alpha Vantage has no data, use yfinance for `get_quote` and `get_series` (e.g. `yf.Ticker(symbol).history(...)`). No key required; good for reducing Alpha Vantage usage.

---

## Database schema for cache

### scan_cache (PostgreSQL)

Stores non-time-series cached responses (quote, fundamentals, news).

| Column | Type | Description |
|--------|------|-------------|
| symbol | VARCHAR | Ticker (e.g. IBM). |
| data_type | VARCHAR | quote, fundamentals, news, etc. |
| interval | VARCHAR (nullable) | Optional interval. |
| payload | JSONB | Raw or normalized response. |
| fetched_at | TIMESTAMPTZ | When the row was last fetched (for TTL). |

**Primary key:** `(symbol, data_type, interval)` (use COALESCE(interval, '') or a single nullable column in key).

**Index:** `(symbol, data_type)` for fast lookup; optionally `fetched_at` for cleanup of old rows.

### symbol_resolution (PostgreSQL)

Maps ISIN to ticker and name.

| Column | Type | Description |
|--------|------|-------------|
| isin | VARCHAR | Primary key. |
| symbol | VARCHAR | Resolved ticker. |
| name | VARCHAR | Company name (from CSV or API). |
| source | VARCHAR | e.g. yahoo, alphavantage. |
| updated_at | TIMESTAMPTZ | Last resolution time (for TTL 30d if desired). |

### ohlcv (TimescaleDB hypertable, optional)

For OHLCV time series; enables compression and fast range queries.

| Column | Type | Description |
|--------|------|-------------|
| time | TIMESTAMPTZ | Partition key. |
| symbol | VARCHAR | Ticker. |
| open | NUMERIC | Open price. |
| high | NUMERIC | High price. |
| low | NUMERIC | Low price. |
| close | NUMERIC | Close price. |
| volume | BIGINT | Volume. |

**Hypertable:** `time` as time dimension; optionally chunk by symbol or time. Compression policy after a certain age (e.g. 7 days) to save space.

**Alternative:** If TimescaleDB is not used, store daily/weekly/monthly series as JSONB in `scan_cache` with `data_type = daily|weekly|monthly`. Simpler but less efficient for large ranges and compression.

---

## Stale-while-revalidate (optional)

- On request, if cache exists but is past TTL, **return the stale payload** immediately to the client/agent.
- **Enqueue a background job** (or fire-and-forget task) to re-fetch from the adapter and update the cache.
- Next request gets fresh data. This improves latency while still refreshing data in the background. Can be added in a second phase without changing the core Scan flow above.
