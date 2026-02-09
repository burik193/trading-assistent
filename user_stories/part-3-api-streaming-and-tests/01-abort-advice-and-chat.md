# User story: Let users cancel advice and chat requests

**Part:** 3 — API, streaming, and tests  
**ID:** 01-abort-advice-and-chat

---

## As a user, I want to cancel a long-running “Get financial advice” or chat reply request, so that I can stop waiting when I change my mind or when the request is taking too long, without having to reload the page.

## What should be done

- **Support abort on the frontend.** The advice SSE (triggered from “Get financial advice”) and the chat SSE (sending a message) currently use `fetch()` without an `AbortController`/`signal`. The frontend should pass an abort signal to these requests so that the user can cancel them. This implies a “Stop” (or “Cancel”) control that the user can click while the request is in progress; when clicked, the ongoing fetch is aborted. After abort, the UI should show a clear state—e.g. “Stopped” or leave the last partial reply visible with an indication that the response was interrupted.

- **Handle abort gracefully.** When the user cancels, the frontend should not treat the abort as a generic error (e.g. do not show “Connection error” as if the server failed). The user should understand that they stopped the request. If the advice pipeline was partially complete (e.g. progress at 50%), the UI can show that progress and indicate that the run was cancelled.

- **Backend behaviour (optional but recommended).** When the client disconnects (e.g. because of abort), the backend should stop work where practical—e.g. close the SSE stream and avoid continuing to run sub-agents or the main agent for a client that is no longer connected. This reduces wasted resources and makes abort feel responsive. The exact mechanism (e.g. detecting disconnect, cancelling in-flight work) is an implementation detail; the outcome is that cancelled requests do not keep consuming backend resources unnecessarily.

## Why

- **User control:** Long-running advice or chat can take tens of seconds; users should be able to back out without losing context or reloading.
- **Resource efficiency:** Stopping backend work on disconnect avoids wasting LLM and API calls for a user who has already left or cancelled.

## Out of scope

- Adding a timeout that auto-cancels after N seconds (can be a separate improvement).
- Changing the SSE event format or the advice/chat API contract; only abort behaviour and UI are in scope.
