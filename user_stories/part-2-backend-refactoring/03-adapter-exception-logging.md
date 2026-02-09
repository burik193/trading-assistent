# User story: Log adapter failures instead of silent continue

**Part:** 2 — Backend refactoring  
**ID:** 03-adapter-exception-logging

---

## As an operator or developer, I want adapter failures (e.g. network errors, rate limits, parse errors) to be logged when they occur, so that we can diagnose why a scan step fell back to the next adapter or failed, without silently swallowing exceptions.

## What should be done

- **Log exceptions in adapter calls.** The adapters (or the scan service when calling them) currently use bare `except Exception: continue` (or equivalent) when a fetch fails, so that the next adapter in the chain can be tried. At least one of these catch sites should be changed so that the exception is logged—for example with `logger.debug("adapter X failed: %s", e)` or `logger.warning(...)`—before continuing. The goal is to make failures visible in logs when running in production or when debugging.

- **Preserve fallback behaviour.** The scan flow should still try the next adapter or return a partial result when one adapter fails; only the visibility of the failure should change. No new user-facing errors or behaviour change is required beyond better observability.

- **Avoid logging sensitive data.** Log messages must not include API keys, full request/response bodies, or other secrets. Log enough context (e.g. adapter name, symbol, exception type and message) to diagnose issues without exposing credentials.

## Why

- **Operability:** In production, “data missing for symbol X” is easier to fix when logs show “Alpha Vantage adapter failed: rate limit” or “Yahoo adapter failed: timeout.”
- **Debugging:** During development and support, silent `continue` makes it hard to understand why a particular data source did not contribute.

## Out of scope

- Adding metrics or tracing (that belongs in the observability part).
- Changing retry logic or rate limiting; only logging of caught exceptions is in scope.
