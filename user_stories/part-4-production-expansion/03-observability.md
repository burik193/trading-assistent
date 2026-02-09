# User story: Structured logging, health/readiness, and metrics

**Part:** 4 — Production expansion  
**ID:** 03-observability

---

## As an operator or developer, I want the backend to support structured logging, a readiness check for dependencies, and optional metrics, so that we can trace requests, know when the app is healthy for load balancers, and monitor performance and errors in production.

## What should be done

- **Structured logging (optional but recommended).** The backend uses plain `logging` without structured fields (e.g. request_id, user_id, symbol). Consider adding structured logging (e.g. JSON output with consistent fields) and correlation IDs so that a single advice or chat flow can be traced across log lines. This helps when debugging “why did this request fail?” or “how long did each step take?”. The exact format and fields are an implementation choice; the outcome is that logs are easier to search and correlate.

- **Readiness check.** `GET /health` currently always returns 200 and does not check the database or other dependencies. Add a readiness check—e.g. a separate `GET /ready` or a query parameter on `/health`—that verifies the application can serve traffic: at minimum, check database connectivity (e.g. a simple query or connection test). Optionally include checks for cache or LLM availability if they are critical. When the check fails, return a non-2xx status so that load balancers and orchestrators can stop sending traffic to the instance until it is healthy again. Document the difference between “liveness” (process is up) and “readiness” (dependencies are OK) if both are exposed.

- **Metrics (optional).** For production, consider exposing metrics (e.g. Prometheus/OpenMetrics) such as request count, latency per endpoint, scan/advice duration, and error counts. This enables dashboards and alerts. The exact technology and metric set can be decided during implementation; the outcome is that key operations are measurable.

## Why

- **Operability:** Load balancers need a reliable readiness signal so that unhealthy instances are taken out of rotation.
- **Debugging:** Correlation IDs and structured logs make it easier to trace a single user flow across services.
- **Monitoring:** Metrics allow teams to spot regressions and capacity issues before users are impacted.

## Out of scope

- Distributed tracing (e.g. OpenTelemetry) unless chosen as the implementation for correlation; the story focuses on logging, readiness, and optional metrics.
- Frontend logging or monitoring; only backend observability is in scope.
