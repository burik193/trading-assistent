# User Stories — Financial Assistant

This folder contains **implementable parts** derived from [project_roadmap.md](../project_roadmap.md). Each part groups related work; inside each part, **user stories** describe what should be done and why (not how).

## Folder structure

| Part | Focus |
|------|--------|
| [part-1-config-and-security](part-1-config-and-security/) | Configuration loading, secrets, CORS |
| [part-2-backend-refactoring](part-2-backend-refactoring/) | Scan service, adapters, agent architecture, data model |
| [part-3-api-streaming-and-tests](part-3-api-streaming-and-tests/) | Abort support, sessions API, automated tests |
| [part-4-production-expansion](part-4-production-expansion/) | Auth, rate limiting, observability, scan behaviour, deployment |
| [part-5-ux](part-5-ux/) | Navigation, loading states, advice flow, chat, sidebar, accessibility |
| [part-6-new-features](part-6-new-features/) | Watchlists, export, multi-symbol comparison, data sources, LangGraph agent |

## How to use

- **Prioritisation:** See the “Suggested priority order” table in [project_roadmap.md](../project_roadmap.md).
- **Scope:** Each story is self-contained; implement in the order listed within a part when dependencies exist.
- **Format:** Stories describe **what** and **why**; implementation details (how) are left to the developer.
