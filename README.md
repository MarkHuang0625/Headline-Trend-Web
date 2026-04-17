# Headline Trend Web

Headline Trend Web is a full-stack market news trend dashboard. It ingests sample financial headlines, classifies them into market themes, and visualizes trend momentum through a React frontend and a FastAPI backend.

## Overview

- Tracks financial headlines with timestamp, source, sentiment, ticker, category, and tags
- Groups stories into themes such as macro, sector, geopolitics, and single-stock news
- Detects emerging and persistent trends across rolling time windows
- Exposes dashboard and headline APIs from a FastAPI service
- Renders a live dashboard with React, TypeScript, Tailwind CSS, and Recharts
- Runs locally without external API keys by seeding mock data and simulating new headlines

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

The backend creates `backend/data/headlines.db` on first run and keeps appending simulated headlines in the background.

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
- `POST /api/ingest/mock`

## How It Works

1. The backend seeds a local SQLite database with sample market headlines.
2. New mock headlines are periodically generated to simulate a live feed.
3. Headlines are classified by category, ticker relevance, and sentiment.
4. Trend aggregation logic scores recurring themes over time windows.
5. The frontend queries the dashboard APIs and renders trend charts, category mixes, and live headline views.

## Development Notes

- `node_modules`, virtual environments, cache files, and the local SQLite database are excluded from version control.
- The app is designed as an MVP, so ingestion is mocked rather than connected to Bloomberg, Reuters, or RSS feeds.
- The repository layer isolates persistence concerns, which makes a future move from SQLite to Postgres straightforward.

## Possible Next Steps

- Replace mock ingestion with RSS feeds or a paid market news API
- Add authentication and saved watchlists
- Add LLM-assisted headline clustering and summarization
- Deploy the frontend and backend as separate services
