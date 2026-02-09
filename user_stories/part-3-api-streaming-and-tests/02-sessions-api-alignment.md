# User story: Align sessions API with docs or add session-scoped chat endpoint

**Part:** 3 — API, streaming, and tests  
**ID:** 02-sessions-api-alignment

---

## As a developer or integrator, I want the API and documentation to match, so that I can rely on AGENTS.md and other docs when building clients or onboarding, and so that we do not promise an endpoint that does not exist.

## What should be done

- **Resolve the mismatch.** AGENTS.md states that chat can be used via `POST /api/chat` or `POST /api/sessions/{id}/messages`. The codebase implements only `POST /api/chat` (body: `session_id`, `message`). There is no `POST /api/sessions/{id}/messages`. The project should choose one of the following and apply it consistently:

  - **Option A — Docs only:** Update AGENTS.md (and any other references) to describe only `POST /api/chat` with `session_id` and `message` in the body. Remove or rephrase the mention of `POST /api/sessions/{id}/messages` so that it is clear this endpoint does not exist (or is optional/future).
  - **Option B — Add the endpoint:** Implement `POST /api/sessions/{session_id}/messages` that accepts a message in the body and behaves like the current chat endpoint for that session (same validation, same streaming, same context loading). Then document both options in AGENTS.md so that clients can use either the global chat endpoint with `session_id` or the session-scoped endpoint.

- **Keep behaviour consistent.** Whichever option is chosen, the actual chat behaviour (streaming, context, history) must remain the same; only the URL and possibly the request shape may differ. Existing frontend use of `POST /api/chat` should continue to work.

## Why

- **Trust in documentation:** Incorrect or outdated API docs lead to wasted effort and integration bugs.
- **RESTfulness (if Option B):** A session-scoped endpoint can be clearer for some clients and tools (e.g. “send message to session X” as a single URL).

## Out of scope

- Changing authentication or authorization for chat; that belongs in the production-expansion part.
- Changing the chat response format or the way session context is loaded; only the endpoint surface and docs are in scope.
