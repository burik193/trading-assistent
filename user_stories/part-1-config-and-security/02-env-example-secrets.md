# User story: No real secrets in .env.example

**Part:** 1 — Configuration and security  
**ID:** 02-env-example-secrets

---

## As a maintainer, I want the example environment file to contain only placeholders and no real API keys, so that we never leak credentials and new developers know what to fill in without using production or personal keys.

## What should be done

- **Replace real keys with placeholders.** The file `.env.example` must not contain any real API key or secret. Every secret (e.g. `ALPHA_VANTAGE_API_KEY`, `GROQ_API_KEY`) should be replaced with a clear placeholder such as `your_alpha_vantage_key_here` or `your_groq_api_key_here`, and the file should be documented so that developers copy it to `.env` and fill in their own values.

- **Rotate any exposed key.** If a real Alpha Vantage (or other) key has ever been committed in `.env.example` or elsewhere in the repo, that key must be considered compromised. It should be rotated or revoked in the provider’s dashboard so that it can no longer be used. The roadmap explicitly calls this out for the Alpha Vantage key that was present in `.env.example`.

- **Prevent future commits of real secrets.** Establish and follow the rule that example and documentation files use placeholders only; real keys belong only in local `.env` (or secure secret stores) and must never be committed.

## Why

- **Security:** Real keys in the repo can be harvested by anyone with read access (including after a clone or fork) and used to consume quota or abuse the service.
- **Onboarding:** Placeholders make it obvious what variables are required and that each developer or environment must supply its own credentials.

## Out of scope

- Implementing secret scanning in CI (can be a separate story elsewhere).
- Changing how the application reads env vars at runtime; only the content of `.env.example` and key rotation are in scope.
