# Quickstart — Financial Assistant

## Prerequisites

- **Python 3.11+** and **uv** (recommended) or pip
- **Node.js 18+** and npm
- **PostgreSQL** (with TimescaleDB extension optional) — or use Docker for DB only

## 1. Environment

From the project root:

```bash
cp .env.example .env
```

Edit `.env` and set at least:

- `GROQ_API_KEY` — required for the LLM (get from [console.groq.com](https://console.groq.com))
- `DATABASE_URL` — e.g. `postgresql://postgres:YOUR_PASSWORD@localhost:5432/analyse_stocks` (use the password you set when installing PostgreSQL on Windows)
- `ALPHA_VANTAGE_API_KEY` — optional; Yahoo is used as fallback

## 2. Backend (Python)

**Always use a virtual environment (uv venv) before running any Python command.** If the project has no venv yet, create one first.

### Option A: Using uv (recommended)

From the project root:

```bash
# Create venv in the project if it does not exist
uv venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (Windows CMD)
.\.venv\Scripts\activate.bat

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies (add any missing packages to backend/requirements.txt)
uv pip install -r backend/requirements.txt

# Run database migrations (PostgreSQL must be running)
cd backend
$env:PYTHONPATH = (Get-Location).Path   # PowerShell
alembic upgrade head
cd ..

# Start the API (must run from backend/ with PYTHONPATH set to backend/)
cd backend
$env:PYTHONPATH = (Get-Location).Path   # PowerShell: set PYTHONPATH to backend dir
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

On Windows CMD from project root:

```cmd
.venv\Scripts\activate
set PYTHONPATH=F:\PycharmProjects\analyse_stocks\backend
cd backend
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be at **http://localhost:8000**. Health check: **http://localhost:8000/health**.

### Start the backend in Dev mode

In **Dev mode** the backend uses mocks only: no Alpha Vantage, Yahoo, or GROQ calls. Use it when you want to run the app without API keys or to avoid rate limits.

**1. Enable Dev mode** (choose one):

- **Environment variable** (for this terminal session only):
  - `DEV_MODE=1` or `DEV_MODE=true` or `DEV_MODE=yes`
  - or `RUN_MODE=dev`
- **In `.env`** (persistent): add `DEV_MODE=1` (or `RUN_MODE=dev`) so every start from this project uses Dev mode until you remove it.

**2. Start the backend** as usual, with Dev mode set:

**PowerShell (from project root, venv active):**

```powershell
cd backend
$env:DEV_MODE = "1"
$env:PYTHONPATH = (Get-Location).Path
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Windows CMD:**

```cmd
cd backend
set DEV_MODE=1
set PYTHONPATH=%CD%
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Linux/macOS:**

```bash
cd backend
export DEV_MODE=1
export PYTHONPATH=$(pwd)
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**If you added `DEV_MODE=1` to `.env`**, you only need:

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

In Dev mode: scan returns mock quote, series, fundamentals, and news; sub-agents and main agent return mock summaries and advice; chat returns a mock reply. No external API or model calls are made.

### Option B: Using pip

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # or source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
set PYTHONPATH=%CD%
alembic upgrade head
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### If packages are missing

Add the missing package to `backend/requirements.txt`, then run:

```bash
uv pip install -r backend/requirements.txt
```

(or `pip install -r backend/requirements.txt` if using pip).

## 3. Frontend (Next.js)

In a **separate terminal** (backend keeps running):

From the project root:

```bash
cd frontend
npm install
npm run dev
```

Frontend will be at **http://localhost:3000**. In development, `/api` is proxied to the backend (see `next.config.js`), so the stock dropdown and other API calls use the same origin and you don't need `NEXT_PUBLIC_API_URL`. If you change `next.config.js`, restart the frontend dev server (`npm run dev`). For production or a different backend URL, set `NEXT_PUBLIC_API_URL` in `.env` or `.env.local`.

## 4. Database (PostgreSQL)

If you don’t have PostgreSQL installed locally, run only the DB with Docker:

```bash
docker-compose up -d postgres
```

**Windows (local PostgreSQL):** Set `DATABASE_URL` in `.env` with your postgres password (e.g. `postgresql://postgres:YOUR_PASSWORD@localhost:5432/analyse_stocks`). Then create the database and run migrations:

```powershell
cd backend
$env:PYTHONPATH = (Get-Location).Path
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/postgres"
python scripts/create_db.py
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/analyse_stocks"
alembic upgrade head
```

Migrations create all tables and load the stocks list from `stocks_list.csv` into the `stocks` table in Postgres.

## 5. Verify

1. **Backend:** Open http://localhost:8000/health — should return `{"status":"ok"}`.
2. **Stocks:** Open http://localhost:8000/api/stocks — should return a list of stocks from Postgres.
3. **Frontend:** Open http://localhost:3000 — select a stock, check dashboard and “Get financial advice” (requires `GROQ_API_KEY` and DB).

## Summary

| Step        | Command |
|------------|---------|
| Venv       | From project root: `uv venv` then activate `.venv` (e.g. `.\.venv\Scripts\Activate.ps1` on Windows) |
| Backend deps | With venv active: `uv pip install -r backend/requirements.txt` |
| Migrations | Start PostgreSQL, then `cd backend`, set `PYTHONPATH` to backend dir, run `alembic upgrade head` |
| Backend    | `cd backend`, set `PYTHONPATH` to backend dir, run `uv run uvicorn main:app --reload --port 8000` |
| Backend (Dev mode) | Same as Backend, but set `DEV_MODE=1` (or add to `.env`) before starting uvicorn; see "Start the backend in Dev mode" above. |
| Frontend   | `cd frontend`, then `npm install` and `npm run dev` |

**Verify:** Backend health (no DB needed): http://localhost:8000/health → `{"status":"ok"}`. Full API (stocks, advice) requires PostgreSQL and migrations.

**Rule:** Always activate the project’s uv venv before running Python. If there is no venv, create one with `uv venv` in the project first. Any missing Python packages must be added to `backend/requirements.txt` and then installed.
