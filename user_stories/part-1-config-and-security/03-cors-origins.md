# User story: CORS origins from environment

**Part:** 1 — Configuration and security  
**ID:** 03-cors-origins

---

## As a deployer, I want allowed CORS origins to be configured via the environment (e.g. a single frontend URL or a list), so that we can run in production without editing code and avoid maintaining a long hardcoded list of localhost ports.

## What should be done

- **Make CORS origins configurable.** The backend currently uses a long hardcoded list of localhost origins (e.g. ports 3000–3010) in `backend/main.py`. This should be replaced (or overridden) by a configuration source that is environment-driven—for example an env var such as `CORS_ORIGINS` containing a comma-separated list of allowed origins, or a single frontend URL. In production, the deployer sets this to the actual frontend origin(s); in development, it can default to a sensible set for localhost or be set explicitly.

- **Preserve development experience.** When running locally, the frontend (e.g. on port 3000) must still be able to call the backend without CORS errors. The chosen mechanism should support both “development” (e.g. several localhost origins or a wildcard for local dev only) and “production” (explicit list of allowed origins).

- **Document the behaviour.** The intended use of the new setting (e.g. `CORS_ORIGINS`) and examples for local vs production should be documented (e.g. in README, quickstart, or .env.example comments) so that deployers know how to configure it.

## Why

- **Production readiness:** Production deployments use a specific frontend URL; hardcoding localhost ports in code is brittle and insecure when the app is exposed.
- **Maintainability:** Adding a new dev port or a new production domain should not require code changes.

## Out of scope

- Changing other CORS options (e.g. methods, headers) unless required to support the above.
- Implementing authentication or CSRF; this story is only about which origins are allowed for CORS.
