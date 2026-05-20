# Headline Trend Web

Headline Trend Web is a full-stack market news trend dashboard. It ingests market news headlines from RSS feeds, classifies them into market themes, and visualizes trend momentum through a React frontend and a FastAPI backend.

## Overview

- Tracks financial headlines with timestamp, source, sentiment, ticker, category, and tags
- Groups stories into themes such as macro, sector, geopolitics, and single-stock news
- Detects emerging and persistent trends across rolling time windows
- Exposes dashboard and headline APIs from a FastAPI service
- Renders a live dashboard with React, TypeScript, Tailwind CSS, and Recharts
- Runs locally without external API keys by polling configurable RSS feeds

## Tech Stack

- Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts
- Backend: FastAPI, SQLite
- Data layer: repository pattern around SQLite storage
- Classification: lightweight keyword and dictionary-based heuristics

## Project Structure

```text
.
├── backend
│   ├── app
│   │   ├── classification.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── sample_data.py
│   │   └── trends.py
│   └── requirements.txt
├── frontend
│   ├── src
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Quick Start

### 1. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend creates `backend/data/headlines.db` on first run and keeps appending RSS headlines in the background.

By default, the backend polls RSS feeds every 5 minutes. You can customize ingestion with environment variables:

```bash
INGESTION_MODE=rss
RSS_POLL_SECONDS=300
RSS_FEED_URLS='CNBC=https://www.cnbc.com/?format=rss,MarketWatch=https://feeds.marketwatch.com/marketwatch/topstories/'
```

Use `INGESTION_MODE=mock` to return to the original simulated feed, or `INGESTION_MODE=off` to disable background ingestion.

The default source set combines MarketWatch with several Google News RSS market queries, so a 24h window can track hundreds of fresh headlines instead of only one outlet's top stories. Dashboard breadth is configurable:

```bash
DASHBOARD_QUERY_LIMIT=500
DASHBOARD_FEED_LIMIT=80
```

Optional LLM trend refinement can clean noisy terms and merge related candidates into clearer market themes:

```bash
OPENAI_API_KEY=sk-...
LLM_TREND_REFINEMENT=auto
OPENAI_MODEL=gpt-4o-mini
```

`LLM_TREND_REFINEMENT=auto` enables refinement only when `OPENAI_API_KEY` is present. Use `LLM_TREND_REFINEMENT=off` to force rule-only trend detection.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

If needed, point the frontend to a custom backend URL:

```bash
echo 'VITE_API_BASE_URL=http://127.0.0.1:8000' > .env.local
```

## API Endpoints

- `GET /health`
- `GET /api/categories`
- `GET /api/headlines`
- `GET /api/dashboard`
- `GET /api/sources`
- `POST /api/ingest/mock`
- `POST /api/ingest/rss`

## How It Works

1. The backend seeds a local SQLite database with sample market headlines as a starter dataset.
2. RSS feeds are periodically polled for real market headlines.
3. Headlines are classified by category, ticker relevance, and sentiment.
4. Trend aggregation logic scores recurring themes over time windows.
5. Optional LLM refinement removes noisy terms and merges related trend candidates into cleaner market themes.
6. The frontend queries the dashboard APIs and renders trend charts, category mixes, and live headline views.

## Development Notes

- `node_modules`, virtual environments, cache files, and the local SQLite database are excluded from version control.
- The app is designed as an MVP, so ingestion uses public RSS feeds rather than paid terminals or API-keyed services.
- The repository layer isolates persistence concerns, which makes a future move from SQLite to Postgres straightforward.

## Possible Next Steps

- Add source-specific parsers for paid market news APIs
- Add authentication and saved watchlists
- Add LLM-assisted headline clustering and summarization
- Deploy the frontend and backend as separate services
