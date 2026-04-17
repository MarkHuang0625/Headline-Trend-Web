from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone

from .classification import STOP_WORDS, tokenize
from .models import CategoryBreakdownItem, HeadlineRecord, TrendItem, TrendPoint


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
        tokens = [token for token in tokenize(headline.headline) if token not in STOP_WORDS]
        unique_tokens = set(tokens)
        bucket = _bucket_label(headline.timestamp, now, window_hours)
        for token in unique_tokens:
            if headline.timestamp >= recent_cutoff:
                recent_counter[token] += 1
            if baseline_cutoff <= headline.timestamp < recent_cutoff:
                baseline_counter[token] += 1
            mentions[token].append(headline.id or 0)
            series[token][bucket] += 1

    items: list[TrendItem] = []
    for keyword, recent_count in recent_counter.items():
        if recent_count < 2:
            continue
        baseline_count = baseline_counter.get(keyword, 0)
        ratio = recent_count / max(0.5, baseline_count)
        score = round((recent_count * 1.4) + ratio, 2)
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

