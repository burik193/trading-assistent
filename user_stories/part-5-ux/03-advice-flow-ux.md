# User story: Progress copy at start and Retry on failure

**Part:** 5 — UX  
**ID:** 03-advice-flow-ux

---

## As a user, I want to see a short message when the advice pipeline has just started (e.g. “Searching for data and preparing analysis…”), and I want a clear failure message with a “Retry” button when the pipeline fails, so that I know the system is working and I can try again without reloading.

## What should be done

- **Message when percent is 0.** The progress bar and step list are already shown during the advice run. When the progress is 0% (pipeline has just started), add a short, user-friendly message—e.g. “Searching for data and preparing analysis…” or similar—so that the user understands the pipeline has started and is not stuck. This can be shown in the same area as the progress (e.g. above or beside the bar) and can be replaced by the first real step name when it arrives.

- **Clear failure message and Retry.** If the advice pipeline fails (e.g. symbol not resolved, sub-agent error, or server error), the UI should show a clear message explaining that the run failed (without exposing technical details) and a “Retry” button. Clicking Retry should trigger the same advice flow again for the current stock. The user should not be left with only a generic error state and no obvious next action.

## Why

- **Feedback:** Users need immediate confirmation that their action (clicking “Get financial advice”) has been registered.
- **Recovery:** A Retry button reduces frustration when failures are transient (e.g. rate limit, network blip).

## Out of scope

- Changing the advice backend or retry logic on the server; only the frontend copy and Retry button behaviour are in scope.
- Adding cancel/abort for the advice run (that is covered in part 3 — API and streaming).
