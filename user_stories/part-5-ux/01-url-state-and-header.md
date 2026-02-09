# User story: URL state for stock/session and human-readable header

**Part:** 5 — UX  
**ID:** 01-url-state-and-header

---

## As a user, I want the selected stock and session to be reflected in the URL and I want the header to show a readable stock name (not only ISIN), so that I can bookmark, share, and refresh the page without losing context, and so that I can tell at a glance which stock I am viewing.

## What should be done

- **URL state.** The app is currently a single page; stock and session selection are kept only in local state. When the user selects a stock or a session, the URL should update (e.g. `/stock/[isin]` or `/session/[id]`, or query params) so that the same view can be restored from the URL. Refreshing the page or opening a bookmarked link should restore the same stock and, when applicable, the same session. The exact URL design (paths vs query, optional session) is an implementation choice; the outcome is that the current context is shareable and survives refresh.

- **Human-readable header.** The main header currently shows “Stock: {selectedIsin}” (the ISIN code). When the stock name and symbol are available (e.g. from the sidebar list or from resolved data), the header should show something like “Stock: {name} ({symbol})” or “Stock: {name}” so that users see a readable label (e.g. “Apple Inc. (AAPL)”) instead of a raw ISIN. If name/symbol are not yet loaded, a fallback (e.g. ISIN or “Loading…”) is acceptable.

## Why

- **Shareability and recovery:** Users can send a link to a colleague or reopen a tab and land on the same stock and session.
- **Clarity:** A readable header reduces confusion when comparing multiple tabs or returning after a break.

## Out of scope

- Changing the sidebar or dashboard layout; only URL state and header content are in scope.
- Adding new routes for unrelated pages (e.g. settings); only stock/session context is in scope.
