# User story: LangGraph-based advice pipeline with tools

**Part:** 6 — New features  
**ID:** 05-langgraph-agent-with-tools

---

## As a product owner or developer, I want the advice pipeline to be implemented as a LangGraph agent that can decide when to fetch data, call tools (e.g. get_quote, get_series, get_news, search_web), and when to synthesize advice, so that we gain flexibility for multi-turn reasoning, optional human-in-the-loop, and future tool-calling features.

## What should be done

- **Implement the pipeline as a graph.** The current advice flow is sequential (scan → sub-agents → main agent) in the advice route. Replace or wrap it with a LangGraph graph that defines: (a) a state schema (e.g. messages, scan_context, summaries, current_step), (b) nodes for orchestration, scan, sub-agents, and main synthesis, and (c) conditional edges so that the orchestrator can decide which node to run next (e.g. fetch data, run sub-agent, or synthesize). The graph should expose the same external behaviour: the advice SSE (progress events and streamed advice) should still be consumable by the existing frontend so that the contract (events, format) does not change.

- **Tools.** The agent should have access to tools that call the scan service and web search (e.g. get_quote, get_series, get_news, search_web). The orchestrator node (or the LLM) should be able to invoke these tools when needed and incorporate results into state. Sub-agents can remain as internal steps or be refactored into tool-calling subgraphs; the outcome is that the agent can decide when to fetch data and when to synthesize, enabling multi-turn and conditional flows.

- **Documentation and dependencies.** architecture.md and AGENTS.md should describe the new graph-based pipeline and how tools are registered and used. The existing `langgraph` dependency should be used; remove or qualify any outdated “sequential pipeline” wording so that docs match the implementation.

## Why

- **Flexibility:** A graph-based pipeline allows branching, retries, and human-in-the-loop without rewriting the whole flow.
- **Tool use:** The agent can fetch data on demand and use web search when the user asks questions that need live or external context.
- **Future features:** Conditional edges and tools make it easier to add new steps or data sources later.

## Out of scope

- Changing the frontend advice or chat UI beyond what is needed to keep the same SSE contract.
- Implementing human-in-the-loop (e.g. approval steps); the story focuses on the graph and tools; human-in-the-loop can be a follow-up.
