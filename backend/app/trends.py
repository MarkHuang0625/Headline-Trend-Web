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


def compute_trends(headlines: list[HeadlineRecord], *, window_hours: int) -> list[TrendItem]:
    if not headlines:
        return []

    now = datetime.now(timezone.utc)
    recent_cutoff = now - timedelta(hours=max(1, window_hours // 4))
    baseline_cutoff = now - timedelta(hours=window_hours)

    recent_counter: Counter[str] = Counter()
    baseline_counter: Counter[str] = Counter()
    mentions: defaultdict[str, list[int]] = defaultdict(list)
    series: defaultdict[str, Counter[str]] = defaultdict(Counter)

    for headline in headlines:
        keywords = _extract_trend_keywords(headline)
        bucket = _bucket_label(headline.timestamp, now, window_hours)
        for keyword in keywords:
            if headline.timestamp >= recent_cutoff:
                recent_counter[keyword] += 1
            if baseline_cutoff <= headline.timestamp < recent_cutoff:
                baseline_counter[keyword] += 1
            mentions[keyword].append(headline.id or 0)
            series[keyword][bucket] += 1

    items: list[TrendItem] = []
    for keyword, recent_count in recent_counter.items():
        minimum_mentions = 2 if _is_theme_label(keyword) else 8
        if recent_count < minimum_mentions or keyword in NOISE_TOKENS:
            continue
        baseline_count = baseline_counter.get(keyword, 0)
        ratio = recent_count / max(1, baseline_count)
        score = round((recent_count * 1.6) + ratio, 2)
        status = "emerging" if ratio >= 1.8 else "persistent"
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
                related_headlines=mentions[keyword][:8],
                series=series_points,
            )
        )

    return sorted(items, key=lambda item: (-item.score, -item.recent_count, item.keyword))[:10]
