# User story: Separate mock logic from production scan flow

**Part:** 2 — Backend refactoring  
**ID:** 02-mock-adapter-separation

---

## As a developer, I want dev-mode and mock behaviour to live outside the main production scan logic, so that the scan flow stays clear, testable, and free of conditional branches that only apply in development.

## What should be done

- **Isolate mock behaviour.** The scan service currently embeds mock helpers (`_mock_quote`, `_mock_series`, `_mock_fundamentals`, `_mock_news`) and dev-mode branches in the same module as production logic. This should be refactored so that mock behaviour is encapsulated—for example in a dedicated `MockAdapter` (or similar) that implements the same adapter interface and returns mock data, or a `dev_mode` adapter that is part of the adapter chain when dev mode is on. The main scan flow should not contain inline mock construction or “if dev_mode then return mock” branches.

- **Preserve dev-mode behaviour.** When the application runs in dev mode (e.g. `DEV_MODE=1` or `RUN_MODE=dev`), the behaviour should remain the same: no real external API or LLM calls, and the dashboard and advice pipeline still receive coherent mock data. Only the structure of the code should change.

- **Keep production path clear.** Production code paths should be easy to read and test without mentally filtering out mock branches. New contributors should be able to understand “what the scan does” without wading through mock logic.

## Why

- **Maintainability:** Mixing mocks and production logic in one place makes the code harder to reason about and refactor.
- **Testing:** A clear production path is easier to unit test; mock behaviour can be tested separately.

## Out of scope

- Changing when or how dev mode is enabled (e.g. env vars); only the structure of mock vs production logic is in scope.
- Adding new mock data shapes; the current mock shape is sufficient for this story.
