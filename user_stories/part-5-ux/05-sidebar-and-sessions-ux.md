# User story: Load more sessions, date/time, and virtualisation for stock list

**Part:** 5 — UX  
**ID:** 05-sidebar-and-sessions-ux

---

## As a user, I want to see when my past chats were created and to load more if the list is long; and I want the stock dropdown to stay performant with very large lists, so that I can find older sessions and use the app smoothly even with many stocks.

## What should be done

- **Past chats: date/time and load more.** The sessions list is limited (e.g. 100 in the API, and a max height in the UI). Show the date and time (or a relative time like “2 hours ago”) for each session in the list so that users can identify when a chat was created. When there are many sessions, add “Load more” or pagination so that users can access older sessions without removing the limit. The exact limit and pagination design (cursor vs offset, “Load more” vs infinite scroll) is an implementation choice; the outcome is that users can find older sessions and see when each was created.

- **Stock dropdown virtualisation (optional).** The stock dropdown search and list work well for moderate list sizes. If the list can grow very large (e.g. 10k+ rows), consider virtualising the list (e.g. render only visible rows) so that scrolling and opening the dropdown remain performant. If the current list size is always small, this item can be deferred; the story is about ensuring the dropdown scales when needed.

## Why

- **Findability:** Date/time and load more make it practical to use many sessions over time.
- **Performance:** Virtualisation prevents the UI from slowing down with very large stock lists.

## Out of scope

- Changing the sessions API contract (e.g. pagination params) beyond what is needed to support “load more”; API changes can be minimal.
- Adding search or filter for sessions; only date/time display and load more (or pagination) are in scope.
