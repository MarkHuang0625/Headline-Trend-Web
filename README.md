# Market Pulse

Market Pulse is a full-stack MVP for tracking and visualizing financial market headline trends in near real time. It ships with a FastAPI backend, SQLite persistence, heuristic NLP classification, and a React/Tailwind dashboard with a terminal-style layout.

## What it does

- Aggregates and stores headlines with timestamp, source, category, ticker, sentiment, and tags
- Classifies headlines into macro, sector, geopolitics, or single-stock buckets
- Detects emerging and persistent trends across rolling windows
- Supports search, category filters, ticker filters, and time-range filters
- Visualizes ranked trends, frequency curves, category mix, and a live headline feed
- Runs without external API keys by seeding sample data and simulating new headlines in the background

## Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts
- Backend: FastAPI, SQLite
- NLP: lightweight keyword and dictionary-based extraction and sentiment scoring

## Project structure

```text
backend/
  app/
frontend/
```

## Backend setup

```bash
cd /Users/markhuang/Documents/Codex/2026-04-17-build-web-apps-plugin-build-web/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend seeds sample headlines into `backend/data/headlines.db` on first run and keeps appending simulated headlines every 20 seconds.

## Frontend setup

```bash
cd /Users/markhuang/Documents/Codex/2026-04-17-build-web-apps-plugin-build-web/frontend
npm install
npm run dev
```

Set the backend URL if needed:

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000' > .env.local
```

## Key endpoints

- `GET /health`
- `GET /api/categories`
- `GET /api/headlines`
- `GET /api/dashboard`
- `POST /api/ingest/mock`

## Notes

- This is an MVP, so ingestion is mocked locally instead of scraping Bloomberg/Reuters directly.
- The backend has clear extension points for RSS feeds, paid APIs, or LLM-based classification.
- SQLite keeps the demo self-contained; swapping to Postgres is straightforward because the repository layer is isolated.

