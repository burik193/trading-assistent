# User story: Config loading via Pydantic

**Part:** 1 — Configuration and security  
**ID:** 01-config-loading

---

## As a developer or operator, I want the application to load and validate configuration from the environment in a predictable way, so that missing or invalid settings are caught at startup and the same behaviour works whether I run from the project root or from the backend directory.

## What should be done

- **Use Pydantic for loading and validation.** The application already defines a `Settings(BaseSettings)` class, but `get_settings()` bypasses Pydantic’s built-in behaviour by passing `os.getenv(...)` explicitly into `Settings(...)`. As a result, values are not loaded from the `.env` file through Pydantic, and validation is effectively skipped. The behaviour should be changed so that configuration is loaded and validated by Pydantic (e.g. by calling `Settings()` with no arguments, or by ensuring the same semantics).

- **Resolve `.env` location consistently.** When the app is run from the `backend/` directory, Pydantic’s relative `env_file = ".env"` is resolved against the current working directory. A `.env` file in the project root may then not be found. The config should either assume a fixed place for `.env` (e.g. project root) or use an absolute path derived from the config module so that the same `.env` is used regardless of where the process is started.

- **Preserve existing settings.** All current settings (e.g. `groq_api_key`, `database_url`, `alpha_vantage_api_key`, `dev_mode`, etc.) should remain available and behave the same from the rest of the application; only the loading mechanism and validation should change.

## Why

- **Correctness:** Invalid or missing required settings should fail fast at startup with clear errors, not at runtime.
- **Portability:** Running from `backend/` or from project root should yield the same config source so that local and CI environments behave consistently.
- **Twelve-Factor alignment:** Configuration from the environment (and a single `.env` when used) is a standard practice for deployability and security.

## Out of scope

- Changing which settings exist or their types.
- Introducing a new config file format (e.g. YAML); the scope is env + `.env` only.
