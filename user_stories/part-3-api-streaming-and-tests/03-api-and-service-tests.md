# User story: Add automated tests for API and core services

**Part:** 3 — API, streaming, and tests  
**ID:** 03-api-and-service-tests

---

## As a developer or maintainer, I want the backend to have automated tests for the main API routes and core services, so that we can refactor and add features with confidence and catch regressions before they reach production.

## What should be done

- **API route tests.** Add tests that call the main FastAPI endpoints (e.g. using FastAPI’s `TestClient`) and assert on status codes and response shape. At minimum, cover: health, list stocks, get series, get metrics, list sessions, get session. Optionally cover advice and chat with mocked scan/LLM so that tests do not depend on external APIs or real LLM calls. The goal is to ensure that the API contract (paths, parameters, response structure) remains valid and that obvious errors (e.g. 500 on valid input) are caught.

- **Unit tests for core services.** Add unit tests for the main logic in: scan_service (e.g. cache hit/miss, TTL, adapter fallback behaviour with mocks), forecast_service (e.g. trend and band computation from a fixed series), and response_sanitizer (e.g. that provider-specific error messages are sanitised for users). These tests should not call real external APIs or the database unless necessary; use mocks or in-memory fixtures where possible.

- **CI integration (recommended).** Run these tests in CI (e.g. on every push or PR) so that failing tests block or warn before merge. Document how to run the test suite locally (e.g. `pytest` from the backend directory).

## Why

- **Stability:** Regressions in API or scan/forecast logic are caught by tests instead of users.
- **Refactoring safety:** When changing config loading, adapters, or the advice pipeline, tests provide a safety net.

## Out of scope

- Full integration tests that hit a real database or external APIs (can be a separate, optional suite).
- Frontend tests (see the next story in this part).
- Performance or load testing; this story is about correctness and contract stability.
