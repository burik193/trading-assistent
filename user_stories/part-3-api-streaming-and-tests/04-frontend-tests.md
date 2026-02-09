# User story: Add frontend unit or E2E tests for critical flows

**Part:** 3 — API, streaming, and tests  
**ID:** 04-frontend-tests

---

## As a developer or maintainer, I want the frontend to have automated tests for at least the critical user flows, so that we can change UI and components without silently breaking selection, advice, or chat.

## What should be done

- **Define critical flows.** The project already has some test hooks (e.g. `data-testid` in the sidebar). Identify the flows that matter most—e.g. “select a stock and see dashboard,” “run Get financial advice and see progress and result,” “open a session and send a chat message”—and ensure they are covered by tests.

- **Add tests.** Implement either (or both): (a) unit tests for key components (e.g. with React Testing Library or similar), using mocked API responses so that components render and behave as expected; or (b) E2E tests (e.g. Playwright) that drive the app in a browser, optionally against a mocked or test backend, and assert that the user can complete the critical flows. The choice of unit vs E2E can depend on project preferences and CI constraints; the outcome is that critical flows are automated.

- **Run tests in CI (recommended).** Frontend tests should run in CI (e.g. on every push or PR) so that UI regressions are caught before merge. Document how to run the frontend test suite locally.

## Why

- **Confidence:** Changing the sidebar, dashboard, or chat components should not accidentally break stock selection or advice display.
- **Documentation:** Tests act as executable specifications for how the UI is supposed to behave.

## Out of scope

- Visual regression testing (e.g. screenshot diff); only behavioural and flow coverage is in scope.
- Testing every edge case or every component; the focus is on critical paths (selection, advice, chat).
