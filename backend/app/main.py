from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
from itertools import cycle
import os

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from .feeds import FeedHeadline, configured_sources, fetch_feed_headlines, last_fetch_report
from .llm_refinement import llm_refinement_enabled, refine_trends_with_llm
from .models import DashboardResponse, HeadlineRecord, TrendItem
from .nlp import compute_embedding_trends, nlp_mode, nlp_models_enabled, nlp_trends_enabled
from .nlp.registry import ensure_models_loaded, model_load_error
from .repository import HeadlineRepository
from .sample_data import MOCK_LIVE_VARIANTS
from .trends import compute_category_breakdown, compute_trends


repository = HeadlineRepository()
mock_stream = cycle(MOCK_LIVE_VARIANTS)
stream_task: asyncio.Task[None] | None = None
INGESTION_MODE = os.getenv("INGESTION_MODE", "rss").lower()
RSS_POLL_SECONDS = int(os.getenv("RSS_POLL_SECONDS", "300"))
DASHBOARD_QUERY_LIMIT = int(os.getenv("DASHBOARD_QUERY_LIMIT", "500"))
DASHBOARD_FEED_LIMIT = int(os.getenv("DASHBOARD_FEED_LIMIT", "80"))


async def simulate_live_ingestion() -> None:
    while True:
        item = next(mock_stream)
        repository.insert_headline(headline=item["headline"], source=item["source"])
        await asyncio.sleep(20)


def ingest_feed_headlines() -> list[HeadlineRecord]:
    records: list[HeadlineRecord] = []
    for item in fetch_feed_headlines():
        records.append(_insert_feed_headline(item))
    return records


def _insert_feed_headline(item: FeedHeadline) -> HeadlineRecord:
    return repository.insert_headline(
        headline=item.headline,
        source=item.source,
        timestamp=item.timestamp,
        url=item.url,
        external_id=item.external_id,
    )


async def warm_nlp_models() -> None:
    if nlp_models_enabled():
        await asyncio.to_thread(ensure_models_loaded)


async def poll_rss_ingestion() -> None:
    while True:
        await asyncio.to_thread(ingest_feed_headlines)
        await asyncio.sleep(RSS_POLL_SECONDS)


@asynccontextmanager
async def lifespan(_: FastAPI):
    global stream_task
    asyncio.create_task(warm_nlp_models())
    if INGESTION_MODE == "mock":
        stream_task = asyncio.create_task(simulate_live_ingestion())
    elif INGESTION_MODE == "off":
        stream_task = None
    else:
        stream_task = asyncio.create_task(poll_rss_ingestion())
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
    return {
        "status": "ok",
        "ingestion_mode": INGESTION_MODE,
        "nlp_mode": nlp_mode(),
    }


@app.get("/api/sources")
def sources() -> dict[str, object]:
    return {
        "ingestion_mode": INGESTION_MODE,
        "nlp_mode": nlp_mode(),
        "nlp_trend_clustering": nlp_trends_enabled(),
        "nlp_models_ready": _nlp_models_ready(),
        "nlp_model_error": model_load_error(),
        "llm_trend_refinement": llm_refinement_enabled(),
        "rss_poll_seconds": RSS_POLL_SECONDS,
        "dashboard_query_limit": DASHBOARD_QUERY_LIMIT,
        "dashboard_feed_limit": DASHBOARD_FEED_LIMIT,
        "rss_sources": configured_sources(),
        "last_fetch": last_fetch_report(),
    }


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
        limit=DASHBOARD_QUERY_LIMIT,
    )
    trends = _compute_dashboard_trends(filtered, window_hours=window_hours)
    trends = refine_trends_with_llm(filtered, trends)
    return DashboardResponse(
        generated_at=datetime.now(timezone.utc),
        window_hours=window_hours,
        tracked_headline_count=len(filtered),
        trends=trends,
        category_breakdown=compute_category_breakdown(filtered),
        headlines=_dashboard_headlines(filtered, trends),
        available_tickers=repository.available_tickers(),
    )


def _dashboard_headlines(
    filtered: list[HeadlineRecord],
    trends: list[TrendItem],
    *,
    extra_related: int = 40,
) -> list[HeadlineRecord]:
    """Include trend-related IDs even when they fall outside the latest feed slice."""
    by_id = {headline.id: headline for headline in filtered if headline.id is not None}
    feed: list[HeadlineRecord] = []
    seen: set[int] = set()

    for headline in filtered[:DASHBOARD_FEED_LIMIT]:
        if headline.id is None or headline.id in seen:
            continue
        feed.append(headline)
        seen.add(headline.id)

    for trend in trends:
        for headline_id in trend.related_headlines:
            if len(feed) >= DASHBOARD_FEED_LIMIT + extra_related:
                break
            if headline_id in seen:
                continue
            record = by_id.get(headline_id)
            if record is None:
                continue
            feed.append(record)
            seen.add(headline_id)

    return feed


def _nlp_models_ready() -> bool | None:
    if not nlp_models_enabled():
        return True
    if model_load_error():
        return False
    from .nlp.registry import embedding_model, sentiment_pipeline, zero_shot_pipeline

    return any(
        pipeline.cache_info().currsize > 0
        for pipeline in (sentiment_pipeline, zero_shot_pipeline, embedding_model)
    )


def _compute_dashboard_trends(headlines: list[HeadlineRecord], *, window_hours: int) -> list[TrendItem]:
    if nlp_trends_enabled() and ensure_models_loaded():
        try:
            embedded = compute_embedding_trends(headlines, window_hours=window_hours)
            if embedded:
                return embedded
        except Exception:
            pass
    return compute_trends(headlines, window_hours=window_hours)


@app.post("/api/ingest/mock", response_model=HeadlineRecord)
def ingest_mock() -> HeadlineRecord:
    item = next(mock_stream)
    return repository.insert_headline(headline=item["headline"], source=item["source"])


@app.post("/api/ingest/rss", response_model=list[HeadlineRecord])
async def ingest_rss() -> list[HeadlineRecord]:
    return await asyncio.to_thread(ingest_feed_headlines)
