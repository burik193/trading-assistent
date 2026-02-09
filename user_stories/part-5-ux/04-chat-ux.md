# User story: Streaming indicator, Stop, Retry, and empty-session copy

**Part:** 5 — UX  
**ID:** 04-chat-ux

---

## As a user, I want to see when the assistant is typing, to be able to stop a long reply, to retry when a message fails, and to see clear copy when no session exists yet, so that chat feels responsive and I can recover from errors or change my mind.

## What should be done

- **Streaming indicator.** Incoming tokens are appended to the last assistant message. Add a subtle indicator that the assistant is still “typing”—e.g. highlight the streaming message, a “Assistant is typing…” label, or a cursor/ellipsis—so that the user knows the reply is in progress and not finished.

- **Stop button.** When the user is waiting for a chat reply, they should be able to cancel the request (e.g. a “Stop” button that appears while the stream is active). After stop, the UI should show the partial reply that was received and a clear “Stopped” or “Cancelled” state so the user understands the reply was interrupted. (Implementation of abort is in part 3; this story is about the UX of the Stop button and the stopped state.)

- **Retry on error.** When a chat message fails (e.g. network or server error), offer a “Retry” control for that message so the user can resend without retyping. The retry should send the same user message again and replace or append the failed attempt’s outcome.

- **Empty-session copy.** When no session exists yet (e.g. user has not run “Get financial advice”), the copy “Run ‘Get financial advice’ to open chat” (or similar) should remain and be clearly visible when the chat panel is open. This guides the user to the right first action.

## Why

- **Clarity:** A typing indicator and stopped state reduce uncertainty during streaming.
- **Recovery:** Retry gives users a way to recover from transient failures.
- **Onboarding:** Empty-session copy directs new users to the correct flow.

## Out of scope

- Changing the chat API or streaming format; only the frontend presentation and controls are in scope.
- Implementing the abort signal and backend disconnect handling; that is in part 3.
