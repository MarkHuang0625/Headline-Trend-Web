from datetime import datetime

from pydantic import BaseModel, Field


class HeadlineRecord(BaseModel):
    id: int | None = None
    headline: str
    source: str
    timestamp: datetime
    category: str
    ticker: str | None = None
    sentiment: str
    tags: list[str] = Field(default_factory=list)


class TrendPoint(BaseModel):
    bucket: str
    count: int


class TrendItem(BaseModel):
    keyword: str
    recent_count: int
    baseline_count: int
    score: float
    status: str
    related_headlines: list[int]
    series: list[TrendPoint]


class CategoryBreakdownItem(BaseModel):
    category: str
    count: int


class DashboardResponse(BaseModel):
    generated_at: datetime
    window_hours: int
    trends: list[TrendItem]
    category_breakdown: list[CategoryBreakdownItem]
    headlines: list[HeadlineRecord]
    available_tickers: list[str]

