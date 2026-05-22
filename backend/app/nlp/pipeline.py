from __future__ import annotations

from dataclasses import dataclass

from ..classification import (
    classify_category as classify_category_rules,
    classify_sentiment as classify_sentiment_rules,
    extract_ticker,
)
from .category import classify_category_zero_shot
from .config import nlp_mode, nlp_models_enabled
from .registry import ensure_models_loaded, model_load_error
from .sentiment import classify_sentiment_finbert


@dataclass(frozen=True)
class HeadlineAnalysis:
    category: str
    sentiment: str
    ticker: str | None
    tags: list[str]
    method: str


def analyze_headline(text: str) -> HeadlineAnalysis:
    mode = nlp_mode()
    if mode == "rules" or not nlp_models_enabled():
        category, tags = classify_category_rules(text)
        return HeadlineAnalysis(
            category=category,
            sentiment=classify_sentiment_rules(text),
            ticker=extract_ticker(text),
            tags=tags,
            method="rules",
        )

    if not ensure_models_loaded():
        category, tags = classify_category_rules(text)
        return HeadlineAnalysis(
            category=category,
            sentiment=classify_sentiment_rules(text),
            ticker=extract_ticker(text),
            tags=[*tags, "nlp_fallback"],
            method=f"rules_fallback:{model_load_error()}",
        )

    ticker = extract_ticker(text)
    if mode == "hybrid":
        category, tags = classify_category_rules(text)
        sentiment = classify_sentiment_finbert(text)
        method = "hybrid"
    else:
        category, tags = classify_category_zero_shot(text)
        sentiment = classify_sentiment_finbert(text)
        method = "models"

    if ticker:
        category = "single_stock"
        if ticker not in tags:
            tags = [*tags, ticker]

    return HeadlineAnalysis(
        category=category,
        sentiment=sentiment,
        ticker=ticker,
        tags=sorted(set(tags)),
        method=method,
    )
