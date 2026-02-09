# User story: Align docs and plan for advice pipeline (LangGraph vs sequential)

**Part:** 2 — Backend refactoring  
**ID:** 04-agent-architecture-clarity

---

## As a developer or stakeholder, I want the documentation and code to clearly reflect how the advice pipeline works today, and to have a clear plan if we move to a LangGraph-based agent, so that we avoid confusion between “LangGraph agent” (mentioned in docs and requirements) and the current sequential implementation.

## What should be done

- **Align documentation with implementation.** The project references a “LangGraph agent” in docs and includes `langgraph` in requirements, but the advice pipeline is implemented as a sequential flow in the advice route (scan → sub-agents → main agent) with no `StateGraph`, conditional edges, or tool-calling loop. Documentation (e.g. architecture.md, AGENTS.md, README) should describe the current behaviour accurately—e.g. “sequential advice pipeline” or “advice route with sub-agents”—so that readers are not led to expect a LangGraph graph.

- **Decide and document the path forward.** The project should have a stated direction: either (a) keep the sequential pipeline and remove or qualify LangGraph references until a future migration, or (b) plan a migration to a LangGraph-based pipeline (when, why, and what stays the same—e.g. SSE contract). This can be a short section in the roadmap or architecture (e.g. “Current: sequential; Future: LangGraph for tools and branching”). The actual implementation of a LangGraph pipeline belongs in the “new features” part; this story is about clarity and planning.

- **No mandatory code change.** If the only change is to docs and a short “plan” section, that is sufficient. Code changes (e.g. removing `langgraph` from requirements) are optional and should follow the decided direction.

## Why

- **Clarity:** New contributors and tools (e.g. AI agents) reading the repo should not assume a LangGraph graph exists when it does not.
- **Prioritisation:** An explicit plan helps decide whether to invest in a LangGraph migration (for tools, branching, human-in-the-loop) or to keep the current design and simplify dependencies.

## Out of scope

- Implementing the LangGraph-based pipeline (see part 6 — new features).
- Changing the external behaviour of the advice endpoint (SSE, progress, advice stream); only documentation and planning are in scope.
