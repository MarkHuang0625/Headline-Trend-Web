from __future__ import annotations

from collections import Counter, defaultdict
import re
from datetime import datetime, timedelta, timezone

from .classification import STOP_WORDS, tokenize
from .models import CategoryBreakdownItem, HeadlineRecord, TrendItem, TrendPoint


NOISE_TOKENS = {
    "higher",
    "lower",
    "lead",
    "leads",
    "push",
    "pushes",
    "commentary",
    "close",
    "latest",
    "update",
    "market",
    "markets",
    "stock",
    "stocks",
    "share",
    "shares",
    "trading",
    "trade",
    "trades",
    "investor",
    "investors",
    "investment",
    "buy",
    "sell",
    "hold",
    "watch",
    "need",
    "know",
    "today",
    "yesterday",
    "week",
    "year",
    "years",
    "amid",
    "among",
    "around",
    "after",
    "before",
    "into",
    "over",
    "under",
    "more",
    "most",
    "some",
    "other",
    "these",
    "those",
    "first",
    "second",
    "third",
    "this",
    "that",
    "your",
    "what",
    "when",
    "will",
    "with",
    "says",
    "said",
    "make",
    "made",
    "gets",
    "here",
    "could",
    "would",
    "should",
    "down",
    "falls",
    "rise",
    "rises",
    "surge",
    "surges",
    "rebound",
    "outperform",
    "underperform",
    "prediction",
    "predictions",
    "research",
    "chair",
    "risk",
    "risks",
    "upside",
    "growth",
    "earnings",
    "options",
    "shows",
    "show",
    "report",
    "reports",
    "analysis",
    "motley",
    "fool",
    "wall",
    "street",
    "investing",
    "investopedia",
    "marketwatch",
    "yahoo",
    "finance",
    "reuters",
    "bloomberg",
    "cnbc",
    "barrons",
    "seeking",
    "alpha",
    "benzinga",
    "zacks",
    "morningstar",
    "aol",
    "msn",
    "forbes",
    "business",
    "insider",
    "stockstory",
    "simplywall",
    "blackrock",
    "tradingview",
    "chartmill",
    "kalkine",
    "media",
    "news",
    "press",
}

THEME_KEYWORDS: dict[str, set[str]] = {
    "rate pressure": {
        "rate",
        "rates",
        "fed",
        "inflation",
        "treasury",
        "yield",
        "yields",
        "bond",
        "bonds",
        "mortgage",
        "tightening",
    },
    "AI chips": {
        "ai",
        "artificial",
        "intelligence",
        "chip",
        "chips",
        "semiconductor",
        "semiconductors",
        "nvidia",
        "nvda",
        "compute",
    },
    "software demand": {
        "software",
        "cloud",
        "infrastructure",
        "server",
        "datacenter",
        "datacenters",
        "servicenow",
        "snowflake",
    },
    "oil supply risk": {
        "energy",
        "oil",
        "crude",
        "refinery",
        "fuel",
        "opec",
        "hormuz",
        "chevron",
        "exxon",
        "xom",
    },
    "banking stress": {
        "bank",
        "banks",
        "lender",
        "lenders",
        "financial",
        "deutsche",
        "jpmorgan",
        "jpm",
    },
    "geopolitical risk": {
        "tariff",
        "tariffs",
        "sanction",
        "sanctions",
        "iran",
        "china",
        "russia",
        "war",
        "conflict",
        "geopolitical",
    },
    "Japan policy": {"boj", "japan", "yen"},
    "EV demand": {"ev", "evs", "auto", "autos", "vehicle", "vehicles", "tesla"},
}


def _clean_tokens(text: str) -> list[str]:
    tokens = []
    for token in tokenize(text):
        normalized = re.sub(r"[^a-z]", "", token.lower())
        if len(normalized) < 4:
            continue
        if normalized in STOP_WORDS or normalized in NOISE_TOKENS:
            continue
        tokens.append(normalized)
    return tokens


def _extract_trend_keywords(headline: HeadlineRecord) -> set[str]:
    cleaned_tokens = set(_clean_tokens(headline.headline))
    matched_themes = {
        theme
        for theme, keywords in THEME_KEYWORDS.items()
        if cleaned_tokens & keywords
    }
    if matched_themes:
        return matched_themes
    return cleaned_tokens


def _is_theme_label(keyword: str) -> bool:
    return keyword in THEME_KEYWORDS


def _bucket_label(timestamp: datetime, now: datetime, window_hours: int) -> str:
    bucket_minutes = max(15, int(window_hours * 60 / 8))
    bucket_time = timestamp.replace(second=0, microsecond=0)
    minute_slot = (bucket_time.minute // bucket_minutes) * bucket_minutes
    bucket_time = bucket_time.replace(minute=minute_slot)
    return bucket_time.strftime("%H:%M")


def compute_category_breakdown(headlines: list[HeadlineRecord]) -> list[CategoryBreakdownItem]:
    counts = Counter(item.category for item in headlines)
    return [
        CategoryBreakdownItem(category=category, count=count)
        for category, count in counts.most_common()
    ]


def trend_window_cutoffs(window_hours: int, *, now: datetime | None = None) -> tuple[datetime, datetime]:
    """Return (window_start, recent_start) using the full selected window."""
    resolved_now = now or datetime.now(timezone.utc)
    slice_hours = max(0.5, window_hours / 2)
    recent_cutoff = resolved_now - timedelta(hours=slice_hours)
    baseline_cutoff = resolved_now - timedelta(hours=window_hours)
    return baseline_cutoff, recent_cutoff


def trend_count_windows(
    headlines: list[HeadlineRecord],
    window_hours: int,
    *,
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    """Return (range_start, recent_start) for recent/baseline counts.

    When headlines only cover part of the selected window (common after RSS
    batch ingests), split the actual data span in half instead of splitting an
    empty earlier window.
    """
    resolved_now = now or datetime.now(timezone.utc)
    window_start = resolved_now - timedelta(hours=window_hours)
    timestamps = [headline.timestamp for headline in headlines if headline.timestamp >= window_start]
    if len(timestamps) < 2:
        return trend_window_cutoffs(window_hours, now=resolved_now)

    data_start = max(window_start, min(timestamps))
    data_end = max(timestamps)
    span = data_end - data_start
    if span < timedelta(minutes=45):
        return trend_window_cutoffs(window_hours, now=resolved_now)

    midpoint = data_start + span / 2
    return data_start, midpoint


def _keyword_tokens(keyword: str) -> set[str]:
    return {token for token in keyword.lower().split() if len(token) > 2}


def _normalize_trend_label(keyword: str) -> str:
    seen: list[str] = []
    for token in keyword.lower().split():
        if token not in seen:
            seen.append(token)
    return " ".join(seen[:4]) or keyword


def _trends_overlap(a: TrendItem, b: TrendItem) -> bool:
    tokens_a = _keyword_tokens(a.keyword)
    tokens_b = _keyword_tokens(b.keyword)
    if tokens_a and tokens_b:
        union = tokens_a | tokens_b
        jaccard = len(tokens_a & tokens_b) / len(union)
        if jaccard >= 0.55:
            return True
        if tokens_a <= tokens_b or tokens_b <= tokens_a:
            return True

    related_a = set(a.related_headlines)
    related_b = set(b.related_headlines)
    if not related_a or not related_b:
        return False
    overlap = len(related_a & related_b)
    smaller = min(len(related_a), len(related_b))
    return overlap / smaller >= 0.45


def _merge_series(a: TrendItem, b: TrendItem) -> Counter[str]:
    merged: Counter[str] = Counter()
    for point in a.series + b.series:
        merged[point.bucket] += point.count
    return merged


def _merge_trend_pair(keep: TrendItem, other: TrendItem) -> TrendItem:
    merged_series = _merge_series(keep, other)
    recent_count, baseline_count = trend_counts_from_buckets(merged_series)
    related_headlines: list[int] = []
    seen: set[int] = set()
    for headline_id in keep.related_headlines + other.related_headlines:
        if headline_id in seen:
            continue
        seen.add(headline_id)
        related_headlines.append(headline_id)

    keyword = _normalize_trend_label(keep.keyword)
    other_keyword = _normalize_trend_label(other.keyword)
    if len(other_keyword.split()) > len(keyword.split()):
        keyword = other_keyword

    ratio = recent_count / max(1, baseline_count)
    score = round((recent_count * 1.8) + ratio, 2)
    status = "emerging" if baseline_count == 0 or ratio >= 1.5 else "persistent"
    return TrendItem(
        keyword=keyword,
        recent_count=recent_count,
        baseline_count=baseline_count,
        score=max(keep.score, other.score, score),
        status=status,
        related_headlines=related_headlines[:24],
        series=[
            TrendPoint(bucket=bucket, count=count)
            for bucket, count in sorted(merged_series.items())
        ],
    )


def merge_similar_trends(trends: list[TrendItem]) -> list[TrendItem]:
    ordered = sorted(trends, key=lambda item: (-item.score, -item.recent_count))
    merged: list[TrendItem] = []

    for trend in ordered:
        combined = False
        for index, existing in enumerate(merged):
            if _trends_overlap(existing, trend):
                merged[index] = _merge_trend_pair(existing, trend)
                combined = True
                break
        if not combined:
            merged.append(
                TrendItem(
                    keyword=_normalize_trend_label(trend.keyword),
                    recent_count=trend.recent_count,
                    baseline_count=trend.baseline_count,
                    score=trend.score,
                    status=trend.status,
                    related_headlines=trend.related_headlines,
                    series=trend.series,
                )
            )

    return sorted(merged, key=lambda item: (-item.score, -item.recent_count, item.keyword))[:10]


def trend_counts_from_buckets(series: Counter[str]) -> tuple[int, int]:
    """Split chart buckets in half so recent/baseline match the frequency curve."""
    ordered = sorted(series.items(), key=lambda item: item[0])
    if not ordered:
        return 0, 0
    if len(ordered) == 1:
        return ordered[0][1], 0

    midpoint = max(1, len(ordered) // 2)
    baseline = sum(count for _, count in ordered[:midpoint])
    recent = sum(count for _, count in ordered[midpoint:])
    return recent, baseline


def compute_trends(headlines: list[HeadlineRecord], *, window_hours: int) -> list[TrendItem]:
    if not headlines:
        return []

    now = datetime.now(timezone.utc)

    recent_counter: Counter[str] = Counter()
    baseline_counter: Counter[str] = Counter()
    keyword_members: defaultdict[str, list[HeadlineRecord]] = defaultdict(list)
    mentions: defaultdict[str, list[int]] = defaultdict(list)
    series: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for headline in headlines:
        keywords = _extract_trend_keywords(headline)
        bucket = _bucket_label(headline.timestamp, now, window_hours)
        for keyword in keywords:
            keyword_members[keyword].append(headline)
            mentions[keyword].append(headline.id or 0)
            series[keyword][bucket] += 1

    for keyword, members in keyword_members.items():
        range_start, recent_cutoff = trend_count_windows(members, window_hours, now=now)
        for headline in members:
            if headline.timestamp >= recent_cutoff:
                recent_counter[keyword] += 1
            elif range_start <= headline.timestamp < recent_cutoff:
                baseline_counter[keyword] += 1

    items: list[TrendItem] = []
    for keyword in keyword_members:
        recent_count, baseline_count = trend_counts_from_buckets(series[keyword])
        if recent_count == 0 and baseline_count == 0:
            continue
        minimum_mentions = 2 if _is_theme_label(keyword) else 8
        if recent_count < minimum_mentions or keyword in NOISE_TOKENS:
            continue
        ratio = recent_count / max(1, baseline_count)
        score = round((recent_count * 1.6) + ratio, 2)
        status = "emerging" if baseline_count == 0 or ratio >= 1.5 else "persistent"
        series_points = [
            TrendPoint(bucket=bucket, count=count)
            for bucket, count in sorted(series[keyword].items())
        ]
        items.append(
            TrendItem(
                keyword=keyword,
                recent_count=recent_count,
                baseline_count=baseline_count,
                score=score,
                status=status,
                related_headlines=mentions[keyword][:24],
                series=series_points,
            )
        )

    ranked = sorted(items, key=lambda item: (-item.score, -item.recent_count, item.keyword))
    return merge_similar_trends(ranked)[:10]
