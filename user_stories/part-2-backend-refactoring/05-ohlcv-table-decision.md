# User story: Use or remove the OHLCV table and document cache strategy

**Part:** 2 — Backend refactoring  
**ID:** 05-ohlcv-table-decision

---

## As a developer or operator, I want the database schema and scan/cache behaviour to be consistent and clearly documented, so that we do not maintain an unused table and so that anyone reading the code or scan.md understands where OHLCV series are stored.

## What should be done

- **Resolve the OHLCV table vs scan_cache mismatch.** The schema defines an `ohlcv` table (and architecture/scan docs mention a TimescaleDB hypertable for OHLCV), but the scan service stores OHLCV series only in `scan_cache.payload` (e.g. via `_get_ohlcv_cached` / `_set_ohlcv_cached`). The `ohlcv` table is never written to. The project should choose one of the following and implement it consistently:

  - **Option A — Use the OHLCV table:** Store daily/weekly/monthly series in the `ohlcv` table (with proper hypertable setup and range queries), and have the scan service read/write that table for series data. Document in scan.md how cache keys, TTLs, and series storage work.
  - **Option B — Remove the OHLCV table:** If the project will continue to store series only in `scan_cache.payload`, remove the `ohlcv` table and any migration that creates it (or mark it as deprecated/unused in docs), and update architecture.md and scan.md to state that OHLCV series are stored in `scan_cache` only.

- **Update documentation.** Whichever option is chosen, scan.md and architecture.md should clearly describe where OHLCV data lives, how it is keyed, and how TTL/refresh applies. This avoids confusion for future work (e.g. compression, range queries, or new data types).

## Why

- **Consistency:** An unused table suggests missing or incomplete implementation and can mislead contributors.
- **Operability:** Correct documentation ensures that backups, monitoring, and migrations are designed for the actual data layout.

## Out of scope

- Adding new cache strategies (e.g. stale-while-revalidate); that is a separate story in the production-expansion part.
- Changing TTL values or cache key design beyond what is needed to support Option A or B.
