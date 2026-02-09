# Financial Assistant

Chat-based financial assistant: dashboard (graphs + metrics), "Get financial advice" pipeline with sub-agents, and session-based chat. See [architecture.md](architecture.md) and [scan.md](scan.md).

## Quick start (Windows)

From project root, with venv and PostgreSQL ready:

1. **Backend:** `.\start-backend.ps1` (loads `.env` and starts API on http://localhost:8000)
2. **Frontend:** In a second terminal, `.\start-frontend.ps1` (starts Next.js on http://localhost:3000 or next free port)
3. Open the frontend URL in the browser; select a stock from the dropdown.

See [quickstart.md](quickstart.md) for full setup (venv, migrations, env vars).

## Setup

1. Copy `.env.example` to `.env` and set:
   - `GROQ_API_KEY` (required for LLM)
   - `DATABASE_URL` (e.g. `postgresql://user:password@localhost:5432/analyse_stocks`)
   - `ALPHA_VANTAGE_API_KEY` (for Alpha Vantage; optional if using Yahoo fallback)
   - Optional: `GROQ_API_KEY_FALLBACK` and `GROQ_MODEL_FALLBACK` for fallback LLM; `DEV_MODE=1` or `RUN_MODE=dev` to run with mocks only (no real API or LLM calls). See [quickstart.md](quickstart.md).

2. **Backend (Python 3.11+)**
   - From `backend/`: `pip install -r requirements.txt`
   - Run PostgreSQL (with TimescaleDB extension if desired). Create DB and run migrations:
     - `cd backend && alembic upgrade head`
   - Start API: `uvicorn main:app --reload` (from `backend/` with `PYTHONPATH=.` or run from project root: `cd backend && python -m uvicorn main:app --reload`)

3. **Frontend**
   - From `frontend/`: `npm install && npm run dev`
   - Set `NEXT_PUBLIC_API_URL=http://localhost:8000` if needed

## Docker

From project root:

```bash
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432

Run migrations once after first start (e.g. exec into backend container and run `alembic upgrade head`, or add an init container).

## Usage

1. Select a stock from the sidebar (from `stocks_list.csv`).
2. View the dashboard (graph + colored metrics).
3. Click "Get financial advice" to run the pipeline (progress bar and status steps).
4. After advice streams, use the chat for follow-up questions. Session is saved in the sidebar.
5. New stock = new session; past chats are listed in the sidebar.
