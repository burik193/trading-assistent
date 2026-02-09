# Part 2 — Backend refactoring

Improve scan service, adapters, agent architecture clarity, and data model consistency.

**Source:** project_roadmap.md §1.3, §1.4, §1.5

## User stories in this part

1. [01-adapter-registration.md](01-adapter-registration.md) — Make adapters configurable or registry-based
2. [02-mock-adapter-separation.md](02-mock-adapter-separation.md) — Separate mock logic from production scan flow
3. [03-adapter-exception-logging.md](03-adapter-exception-logging.md) — Log adapter failures instead of silent continue
4. [04-agent-architecture-clarity.md](04-agent-architecture-clarity.md) — Align docs and plan for advice pipeline (LangGraph or sequential)
5. [05-ohlcv-table-decision.md](05-ohlcv-table-decision.md) — Use or remove the OHLCV table and document cache strategy
