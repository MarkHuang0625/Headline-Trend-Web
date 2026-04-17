from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from itertools import cycle

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .models import DashboardResponse, HeadlineRecord
from .repository import HeadlineRepository
from .sample_data import MOCK_LIVE_VARIANTS
from .trends import compute_category_breakdown, compute_trends


repository = HeadlineRepository()
mock_stream = cycle(MOCK_LIVE_VARIANTS)
stream_task: asyncio.Task[None] | None = None


async def simulate_live_ingestion() -> None:
    while True:
        item = next(mock_stream)
        repository.insert_headline(headline=item["headline"], source=item["source"])
        await asyncio.sleep(20)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global stream_task
    stream_task = asyncio.create_task(simulate_live_ingestion())
    try:
        yield
    finally:
        if stream_task:
            stream_task.cancel()
            with suppress(asyncio.CancelledError):
                await stream_task


app = FastAPI(title="Market Pulse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/categories")
def categories() -> dict[str, list[str]]:
    return {
        "categories": ["all", "macro", "single_stock", "sector", "geopolitics"],
        "tickers": repository.available_tickers(),
    }


@app.get("/api/headlines", response_model=list[HeadlineRecord])
def headlines(
    search: str | None = Query(default=None),
    category: str | None = Query(default="all"),
    ticker: str | None = Query(default=None),
    window_hours: int = Query(default=24, ge=1, le=72),
    limit: int = Query(default=80, ge=1, le=200),
) -> list[HeadlineRecord]:
    return repository.list_headlines(
        search=search,
        category=category,
        ticker=ticker,
        hours=window_hours,
        limit=limit,
    )


@app.get("/api/dashboard", response_model=DashboardResponse)
def dashboard(
    search: str | None = Query(default=None),
    category: str | None = Query(default="all"),
    ticker: str | None = Query(default=None),
    window_hours: int = Query(default=24, ge=1, le=72),
) -> DashboardResponse:
    filtered = repository.list_headlines(
        search=search,
        category=category,
        ticker=ticker,
        hours=window_hours,
        limit=200,
    )
    return DashboardResponse(
        generated_at=datetime.now(timezone.utc),
        window_hours=window_hours,
        trends=compute_trends(filtered, window_hours=window_hours),
        category_breakdown=compute_category_breakdown(filtered),
        headlines=filtered[:40],
        available_tickers=repository.available_tickers(),
    )


@app.post("/api/ingest/mock", response_model=HeadlineRecord)
def ingest_mock() -> HeadlineRecord:
    item = next(mock_stream)
    return repository.insert_headline(headline=item["headline"], source=item["source"])
