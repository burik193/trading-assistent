# User story: Keyboard, screen readers, and focus

**Part:** 5 — UX  
**ID:** 06-accessibility

---

## As a user who relies on the keyboard or a screen reader, I want the app to support tab order, Enter/Space for buttons, Escape to close dropdowns, announcements for progress and streaming, and sensible focus after actions, so that I can use the app without a mouse and get live updates announced.

## What should be done

- **Keyboard.** Ensure a logical tab order through the main controls (sidebar, stock dropdown, dashboard, advice button, chat input, etc.). Buttons (including “Get financial advice,” “Retry,” “Stop”) should be activatable with Enter and Space. Dropdowns (e.g. stock picker, session list) should close on Escape so that keyboard users can dismiss them without clicking outside. Where custom controls are used, they should follow the same patterns (focusable, activatable, dismissible).

- **Screen readers.** Use `aria-live` (or equivalent) for regions that update dynamically so that assistive technologies announce changes. At minimum: (a) progress during the advice run (e.g. “Step 3 of 10: Fetching news”) and (b) streaming advice and chat content (e.g. so that new tokens or completed messages are announced). The goal is that users who rely on screen readers get the same information as sighted users when content updates.

- **Focus management.** After “Get financial advice” completes successfully, move focus to a useful next element—e.g. the first line of the advice text or the chat input—so that keyboard users can continue (e.g. scroll the advice or type a follow-up) without extra tabbing. This reduces the number of steps needed to continue the flow.

## Why

- **Inclusion:** Keyboard and screen reader support make the app usable for people with motor or visual impairments.
- **Efficiency:** Good focus and announcements help all users who prefer keyboard or assistive tech.

## Out of scope

- Full WCAG audit or compliance certification; the story focuses on the listed improvements.
- Changing visual design (e.g. contrast, font size) unless required for focus/visibility; only keyboard, live regions, and focus are in scope.
