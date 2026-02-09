# User story: Watchlists and optional price/condition alerts

**Part:** 6 — New features  
**ID:** 01-watchlists-and-alerts

---

## As a user, I want to save a list of favourite symbols (watchlist) and optionally set price or condition alerts (e.g. “Notify when AAPL > 200”), so that I can track my interests in one place and get notified when conditions are met without constantly checking.

## What should be done

- **Watchlists.** Users should be able to maintain one or more watchlists—each a named list of symbols or ISINs. They should be able to add a symbol to a watchlist from the dashboard or sidebar (e.g. “Add to watchlist”) and remove it. When auth exists, watchlists can be scoped to the current user; otherwise they can be scoped to an anonymous id (e.g. local storage) so that the feature works before auth is implemented. The backend should persist watchlists (e.g. `watchlists` and `watchlist_items` tables) and expose APIs to list, create, update, and delete watchlists and their items. The frontend should provide a “Watchlist” panel or view where the user can see their lists and jump to a stock from the list.

- **Optional alerts.** Users should be able to define alerts on a symbol—e.g. “notify when price > 200” or “when price crosses below 50-day average.” The backend should store these (e.g. `alerts` table: symbol, condition, threshold, notified_at, user or anonymous id). A background job or scheduled task should periodically evaluate conditions (e.g. using quote or technical indicator data) and record when an alert fires (e.g. set `notified_at`). Notifications can be in-app (e.g. a badge or list of “triggered alerts”) and optionally email or push in a later phase. The exact condition language (e.g. “above,” “below,” “cross”) and evaluation frequency are implementation choices; the outcome is that users can set conditions and be informed when they are met.

## Why

- **Engagement:** Watchlists and alerts keep users coming back and make the app more useful for daily monitoring.
- **Differentiation:** Many financial apps offer watchlists and alerts; having them aligns with user expectations.

## Out of scope

- Implementing full auth (assume auth can be added separately; watchlists can work with anonymous id first).
- Email or push delivery infrastructure (in-app notification is sufficient for this story; delivery can be a follow-up).
