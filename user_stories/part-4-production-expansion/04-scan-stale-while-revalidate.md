# User story: Serve stale cache and refresh in background (stale-while-revalidate)

**Part:** 4 — Production expansion  
**ID:** 04-scan-stale-while-revalidate

---

## As a user or operator, I want the application to return cached data immediately when it exists but is past TTL, and to refresh it in the background, so that I get a fast response while data is still updated for the next request, and so that we reduce thundering herd when many requests hit at cache expiry.

## What should be done

- **Serve stale on miss.** When a request arrives for a symbol/data_type that has cached data but the cache is past its TTL (stale), the scan service should return the stale payload immediately to the caller (API or advice pipeline) instead of blocking until a fresh fetch completes. The caller can then respond to the user quickly with slightly outdated but valid data.

- **Refresh in background.** When serving stale data, the scan service should trigger a background refresh—e.g. enqueue a task or fire a non-blocking fetch—to update the cache from the adapter. The next request for the same symbol/data_type should see the fresh data (or again stale if the refresh has not yet completed). The exact mechanism (e.g. in-process task, queue, or worker) is an implementation detail; the outcome is that refresh does not block the request that got stale data.

- **Document behaviour.** scan.md already describes stale-while-revalidate as optional. Once implemented, update scan.md to describe when stale is served, when background refresh is triggered, and how TTLs interact with this behaviour.

## Why

- **Perceived latency:** Users see a response quickly instead of waiting for a full external fetch when cache has expired.
- **Resilience:** Thundering herd at expiry (many concurrent requests all hitting the adapter) is reduced because the first request gets stale and triggers one background refresh; others can be served from cache until refresh completes.

## Out of scope

- Changing TTL values or cache key design; only the “serve stale + background refresh” behaviour is in scope.
- Pre-warming or scheduled scan jobs; that can be a separate story (e.g. background scan for popular symbols).
