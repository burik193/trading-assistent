# User story: Per-client rate limiting and input validation

**Part:** 4 — Production expansion  
**ID:** 02-rate-limiting-and-validation

---

## As a deployer or operator, I want the API to enforce per-client rate limits and to validate inputs (e.g. ISIN format) so that we prevent abuse, protect backend and external APIs, and avoid bad data or injection-style issues.

## What should be done

- **API rate limiting.** Today only the Alpha Vantage adapter is rate-limited; the FastAPI app itself does not limit how many requests a single client (e.g. IP or user) can make. Add a mechanism—e.g. middleware or a dependency (such as slowapi or a custom limiter)—to limit the request rate per client (e.g. per IP or per user when auth exists). When the limit is exceeded, the API should return a clear response (e.g. 429 Too Many Requests) so that clients know to back off. The limits and scope (IP vs user) should be configurable so that different environments can tune them.

- **Input validation.** Path and query parameters (e.g. `isin` in stock and advice routes) are currently passed as strings without format checks. Add validation so that invalid or malformed values are rejected with a clear error (e.g. 422) before they reach business logic. For example: validate ISIN format (or a whitelist), validate session IDs are integers, and validate optional query params (e.g. interval, format). Use Pydantic models or explicit regex/format checks so that bad data and injection-style inputs are caught at the boundary.

## Why

- **Stability:** Rate limiting prevents a single client or buggy script from overwhelming the backend or triggering excessive external API usage.
- **Security and data quality:** Validating inputs reduces the risk of malformed data and injection-style issues and gives clients clear feedback.

## Out of scope

- Changing business logic or adapter behaviour; only the API boundary (rate limit and validation) is in scope.
- Implementing CAPTCHA or bot detection; only rate limiting and input validation are in scope.
