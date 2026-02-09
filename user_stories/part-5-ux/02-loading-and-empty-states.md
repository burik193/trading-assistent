# User story: Skeletons and differentiated empty/error states

**Part:** 5 — UX  
**ID:** 02-loading-and-empty-states

---

## As a user, I want loading states to use skeleton placeholders so the layout does not jump, and I want “no data yet” to be clearly different from “error” with suggested actions, so that the app feels responsive and I know what to do when data is missing or failed.

## What should be done

- **Skeleton placeholders for dashboard.** The dashboard currently shows plain “Loading…” text while series and metrics are fetched. Replace or supplement this with skeleton placeholders for the chart area and the metrics grid—e.g. grey blocks or shimmer placeholders that match the approximate layout of the real content. The goal is to avoid a large layout shift when data arrives and to give the user a clear sense that content is loading.

- **Differentiate empty vs error.** When no stock is selected, the message is clear. When series or metrics fail to load (e.g. network error, rate limit), the same generic warning box may be shown as for “no data yet.” The UI should distinguish: (a) “no data yet” (e.g. stock selected but scan not run)—suggest “Get financial advice” to trigger a scan; (b) “error” (e.g. request failed)—show a clear error message and suggest “Try again” or “Try another symbol.” Where possible, provide a single clear action (e.g. “Get financial advice” or “Retry”) so the user knows what to do next.

## Why

- **Perceived performance:** Skeleton loaders make the app feel faster and more polished.
- **Reduced confusion:** Differentiating “no data” from “error” and suggesting actions reduces support burden and improves completion rates.

## Out of scope

- Changing the actual data-fetching logic; only the presentation of loading and empty/error states is in scope.
- Adding new data sources or retry logic in the backend; only frontend UX for existing flows is in scope.
