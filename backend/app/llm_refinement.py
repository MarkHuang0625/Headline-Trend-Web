from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import os
import urllib.error
import urllib.request

from .models import HeadlineRecord, TrendItem, TrendPoint


OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = "gpt-4o-mini"
CACHE_TTL = timedelta(minutes=10)
MAX_TRENDS = 12
MAX_HEADLINES = 40


@dataclass
class CachedRefinement:
    expires_at: datetime
    trends: list[TrendItem]


_cache: dict[str, CachedRefinement] = {}


def llm_refinement_enabled() -> bool:
    configured = os.getenv("LLM_TREND_REFINEMENT", "auto").lower()
    if configured in {"0", "false", "off", "no"}:
        return False
    if configured in {"1", "true", "on", "yes"}:
        return bool(os.getenv("OPENAI_API_KEY"))
    return bool(os.getenv("OPENAI_API_KEY"))


def refine_trends_with_llm(headlines: list[HeadlineRecord], trends: list[TrendItem]) -> list[TrendItem]:
    if not trends or not llm_refinement_enabled():
        return trends

    cache_key = _cache_key(headlines, trends)
    now = datetime.now(timezone.utc)
    cached = _cache.get(cache_key)
    if cached and cached.expires_at > now:
        return cached.trends

    try:
        refined = _request_refinement(headlines, trends)
    except (OSError, KeyError, ValueError, json.JSONDecodeError, urllib.error.URLError):
        return trends

    _cache[cache_key] = CachedRefinement(expires_at=now + CACHE_TTL, trends=refined)
    return refined


def _request_refinement(headlines: list[HeadlineRecord], trends: list[TrendItem]) -> list[TrendItem]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return trends

    payload = {
        "model": os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
        "input": [
            {
                "role": "system",
                "content": (
                    "You clean and group market-news trend candidates. "
                    "Return only meaningful financial-market themes. "
                    "Remove generic language, personal-finance filler, pronouns, and weak terms. "
                    "Prefer concise labels such as 'interest rates', 'oil supply risk', "
                    "'rate pressure', 'banking stress', 'geopolitical risk', or 'AI chips'. "
                    "Do not use publisher names, website names, or broad words like stocks, markets, "
                    "investors, trading, investment, or shares as topic labels."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(_prompt_payload(headlines, trends), ensure_ascii=True),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "trend_refinement",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "noise_terms": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "topics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "label": {"type": "string"},
                                    "keywords": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "headline_ids": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                    },
                                },
                                "required": ["label", "keywords", "headline_ids"],
                            },
                        },
                    },
                    "required": ["noise_terms", "topics"],
                },
            }
        },
    }

    request = urllib.request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        data = json.loads(response.read())

    refinement = json.loads(_response_text(data))
    return _apply_refinement(trends, refinement)


def _prompt_payload(headlines: list[HeadlineRecord], trends: list[TrendItem]) -> dict[str, object]:
    headline_lookup = {headline.id: headline for headline in headlines if headline.id is not None}
    relevant_ids = {
        headline_id
        for trend in trends[:MAX_TRENDS]
        for headline_id in trend.related_headlines
    }
    selected_headlines = [
        headline_lookup[headline_id]
        for headline_id in relevant_ids
        if headline_id in headline_lookup
    ][:MAX_HEADLINES]

    return {
        "candidate_trends": [
            {
                "keyword": trend.keyword,
                "recent_count": trend.recent_count,
                "baseline_count": trend.baseline_count,
                "score": trend.score,
                "related_headline_ids": trend.related_headlines,
            }
            for trend in trends[:MAX_TRENDS]
        ],
        "headlines": [
            {
                "id": headline.id,
                "headline": headline.headline,
                "source": headline.source,
                "category": headline.category,
                "ticker": headline.ticker,
                "tags": headline.tags,
            }
            for headline in selected_headlines
        ],
    }


def _apply_refinement(trends: list[TrendItem], refinement: dict[str, object]) -> list[TrendItem]:
    noise_terms = {
        str(term).strip().lower()
        for term in refinement.get("noise_terms", [])
        if str(term).strip()
    }
    topics = refinement.get("topics", [])
    if not isinstance(topics, list):
        return trends

    trend_by_keyword = {trend.keyword.lower(): trend for trend in trends}
    trend_by_headline: dict[int, list[TrendItem]] = {}
    for trend in trends:
        for headline_id in trend.related_headlines:
            trend_by_headline.setdefault(headline_id, []).append(trend)

    refined: list[TrendItem] = []
    used_keywords: set[str] = set()
    for topic in topics:
        if not isinstance(topic, dict):
            continue
        label = str(topic.get("label", "")).strip().lower()
        if not label or label in noise_terms:
            continue

        keywords = [
            str(keyword).strip().lower()
            for keyword in topic.get("keywords", [])
            if str(keyword).strip()
        ]
        headline_ids = [
            int(headline_id)
            for headline_id in topic.get("headline_ids", [])
            if isinstance(headline_id, int)
        ]

        candidates = [
            trend_by_keyword[keyword]
            for keyword in keywords
            if keyword in trend_by_keyword and keyword not in noise_terms
        ]
        for headline_id in headline_ids:
            candidates.extend(trend_by_headline.get(headline_id, []))
        candidates = _unique_trends(candidates)
        if not candidates:
            continue

        merged = _merge_trends(label, candidates)
        refined.append(merged)
        used_keywords.update(trend.keyword.lower() for trend in candidates)

    for trend in trends:
        keyword = trend.keyword.lower()
        if keyword not in noise_terms and keyword not in used_keywords:
            refined.append(trend)

    return sorted(refined, key=lambda item: (-item.score, -item.recent_count, item.keyword))[:10]


def _merge_trends(label: str, trends: list[TrendItem]) -> TrendItem:
    primary = max(trends, key=lambda trend: (trend.score, trend.recent_count))
    related_headlines = _dedupe_ints(
        headline_id
        for trend in trends
        for headline_id in trend.related_headlines
    )[:8]
    bucket_counts: dict[str, int] = {}
    for trend in trends:
        for point in trend.series:
            bucket_counts[point.bucket] = bucket_counts.get(point.bucket, 0) + point.count

    return primary.model_copy(
        update={
            "keyword": label,
            "recent_count": max(trend.recent_count for trend in trends),
            "baseline_count": max(trend.baseline_count for trend in trends),
            "score": round(max(trend.score for trend in trends), 2),
            "status": "emerging" if any(trend.status == "emerging" for trend in trends) else "persistent",
            "related_headlines": related_headlines,
            "series": [
                TrendPoint(bucket=bucket, count=count)
                for bucket, count in sorted(bucket_counts.items())
            ],
        }
    )


def _response_text(data: dict[str, object]) -> str:
    output_text = data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    for item in data.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if isinstance(content, dict) and content.get("type") == "output_text":
                text = content.get("text")
                if isinstance(text, str):
                    return text
    raise ValueError("OpenAI response did not include output text")


def _cache_key(headlines: list[HeadlineRecord], trends: list[TrendItem]) -> str:
    headline_ids = ",".join(str(headline.id) for headline in headlines[:MAX_HEADLINES])
    trend_keys = ",".join(f"{trend.keyword}:{trend.recent_count}:{trend.baseline_count}" for trend in trends[:MAX_TRENDS])
    return f"{headline_ids}|{trend_keys}"


def _unique_trends(trends: list[TrendItem]) -> list[TrendItem]:
    seen: set[str] = set()
    unique: list[TrendItem] = []
    for trend in trends:
        if trend.keyword in seen:
            continue
        seen.add(trend.keyword)
        unique.append(trend)
    return unique


def _dedupe_ints(values) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
