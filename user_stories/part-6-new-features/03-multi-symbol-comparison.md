# User story: Compare 2–5 symbols in one view

**Part:** 6 — New features  
**ID:** 03-multi-symbol-comparison

---

## As a user, I want to compare metrics and performance of several symbols (e.g. 2–5) in one view—side-by-side charts and common KPIs—so that I can evaluate alternatives or related stocks without switching tabs.

## What should be done

- **Backend support.** The backend should support returning data for multiple symbols in one request. This can be done by reusing existing `get_series` and `get_metrics` per symbol and aggregating the results, or by adding an endpoint (e.g. `GET /api/compare?isins=A,B,C`) that returns aggregated series and metrics for the given ISINs. The response shape should allow the frontend to render multiple series on one chart and a comparison table (e.g. same KPIs for each symbol). Rate limits and cache should still apply per symbol; the implementation should not bypass the scan service.

- **Frontend: compare mode.** The frontend should offer a “Compare” mode or flow where the user can select multiple symbols (e.g. 2–5). In compare mode, the UI should show: (a) one chart with multiple lines (e.g. one line per symbol, normalised or same scale) and (b) a comparison table of key metrics (e.g. P/E, market cap, change %) so that the user can see differences at a glance. The exact layout (e.g. tabs vs single view) is an implementation choice; the outcome is that the user can compare selected symbols in one place.

- **Integration with existing data.** Existing adapters and the scan service already support fetching data per symbol; the comparison feature should use the same cache and TTLs so that comparison does not bypass or duplicate scan logic.

## Why

- **Differentiation:** Comparison is a common need in financial apps and adds clear value.
- **Efficiency:** Users can evaluate several stocks without opening multiple sessions or tabs.

## Out of scope

- Comparing more than a small set (e.g. 2–5) in one view; larger sets can be a future enhancement.
- Changing the scan service or adapter interface beyond what is needed to serve multiple symbols in one response.
