# User story: New data source adapters (e.g. Simfin, FRED, SEC Edgar)

**Part:** 6 — New features  
**ID:** 04-more-data-sources

---

## As a product owner or operator, I want to integrate additional data sources (e.g. fundamentals from Simfin, macro data from FRED, filings from SEC Edgar, or Stooq) so that we diversify providers, reduce dependency on a single API, and enrich the data available to the assistant.

## What should be done

- **Implement new adapters.** Each new source should be implemented as an adapter that conforms to the existing `DataSourceAdapter` interface (or the relevant subset: e.g. `get_quote`, `get_series`, `get_fundamentals`, `get_news`). For example: a `SimfinAdapter` for fundamentals, a `FredAdapter` for macro or reference data, or an adapter that wraps SEC Edgar or Stooq. The adapter should call the external API, normalize the response to the canonical schema used by the scan service, and handle errors and rate limits appropriately. New adapters should live in `backend/app/adapters/` and follow the same patterns as Alpha Vantage and Yahoo.

- **Register and document.** New adapters should be registered with the scan service (or via the config/registry from part 2 — backend refactoring) so that they are used in the chain. architecture.md and scan.md should be updated to list the new adapters and any new data types or TTLs. Optionally, create or update a `research.md` with URLs and API notes for each data source so that future integrations are easier.

- **Scope per source.** The story can be split by source (e.g. one story per adapter). The outcome is that at least one new source is integrated and documented; additional sources can be added incrementally.

## Why

- **Resilience:** Multiple providers reduce the impact of one provider’s outage or rate limits.
- **Richness:** Different sources (e.g. SEC filings, macro data) can improve the quality of advice and analysis.

## Out of scope

- Changing the agent prompts or the way the assistant uses the data; only the data ingestion and adapter layer are in scope.
- Implementing auth or API keys for new sources (use env vars and existing config patterns).
