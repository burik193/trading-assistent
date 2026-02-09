# User story: Add authentication and protect routes

**Part:** 4 — Production expansion  
**ID:** 01-authentication

---

## As a product owner or deployer, I want the application to support authentication (e.g. JWT or session-based) and to restrict access to protected routes, so that only authenticated users can use the API and so that sessions can be scoped to a user when we need multi-tenancy.

## What should be done

- **Introduce authentication.** The application currently has no auth; any client can call all APIs and access all sessions. Add a mechanism for users to authenticate—for example login and refresh endpoints that issue and renew JWT tokens, or session-based auth (e.g. cookie-backed). The chosen mechanism should be documented (e.g. in architecture.md) and should allow the backend to identify the current user (or anonymous) on each request.

- **Protect routes.** Apply authentication checks to the routes that should be protected—e.g. advice, chat, sessions, stocks. Unauthenticated requests to protected routes should receive a 401 (or equivalent) with a clear error. Public routes (e.g. health, or a future “login” page) can remain unprotected. The exact set of protected routes is a product decision; the outcome is that sensitive operations require a valid identity.

- **Optional user-scoping of sessions.** When auth exists, sessions can be associated with a user (e.g. `user_id` on the sessions table). This allows “my chats” to be filtered by user and prepares for multi-user deployment. If the first version of auth does not yet scope sessions, document the intended next step (e.g. “Phase 2: add user_id to sessions and filter list by current user”).

## Why

- **Security:** Production deployments cannot expose advice and chat to unauthenticated clients.
- **Multi-tenancy:** User-scoped sessions enable multiple users to use the same instance without seeing each other’s data.

## Out of scope

- Implementing sign-up, password reset, or OAuth providers; only the backend auth mechanism and route protection are in scope. Frontend login UI can be a separate story.
- Changing the API request/response format for chat or advice beyond adding an `Authorization` header or equivalent.
