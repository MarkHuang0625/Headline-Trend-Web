from __future__ import annotations

from .registry import sentiment_pipeline


_FINBERT_LABELS = {
    "positive": "positive",
    "negative": "negative",
    "neutral": "neutral",
    "bullish": "positive",
    "bearish": "negative",
}


def classify_sentiment_finbert(text: str) -> str:
    result = sentiment_pipeline()(text[:512])[0]
    label = result["label"].lower()
    return _FINBERT_LABELS.get(label, "neutral")
