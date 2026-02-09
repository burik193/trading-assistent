# User story: Export advice and metrics (JSON/CSV/PDF)

**Part:** 6 — New features  
**ID:** 02-export-and-reporting

---

## As a user, I want to export advice and metrics for a stock or a session (e.g. as JSON, CSV, or PDF), so that I can keep a record, share with others, or use the data in other tools.

## What should be done

- **Export by stock.** Users should be able to export data for the current stock—e.g. metrics (fundamentals, technicals) and optionally the latest advice summary. The backend should provide an endpoint (e.g. `GET /api/stocks/{isin}/export?format=json|csv`) that returns the data in the requested format. JSON and CSV should be structured so that the data is easy to consume (e.g. flat key-value for metrics, or tabular rows). The frontend should offer an “Export” control (e.g. button or menu) on the dashboard that triggers the export (e.g. download file or open in new tab).

- **Export by session (optional).** Users should be able to export a session—e.g. the full advice and chat history—as a document. The backend can provide an endpoint (e.g. `GET /api/sessions/{id}/export?format=pdf`) that generates a PDF (or JSON) of the session content. PDF generation can use a server-side library (e.g. WeasyPrint, reportlab) or a headless JS-based solution; the outcome is a downloadable document. The frontend should offer an “Export” option when viewing a session (e.g. in the chat panel or session list).

- **Format and scope.** At least one machine-readable format (JSON or CSV) for stock export and one human-readable format (PDF) for session export should be supported. The exact set of fields (e.g. full scan context vs summary) is an implementation choice; the outcome is that users can get a portable record of their analysis or conversation.

## Why

- **Record-keeping:** Users can archive advice and metrics for compliance or personal reference.
- **Sharing:** Export makes it easy to share analysis with colleagues or advisors without giving access to the app.

## Out of scope

- Scheduling or automating exports (e.g. daily report); only on-demand export is in scope.
- Changing the advice or chat data model; only the export shape and format are in scope.
