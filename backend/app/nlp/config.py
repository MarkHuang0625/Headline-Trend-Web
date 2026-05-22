from __future__ import annotations

import os


def nlp_mode() -> str:
    """rules | models | hybrid"""
    return os.getenv("NLP_MODE", "models").lower()


def nlp_models_enabled() -> bool:
    return nlp_mode() in {"models", "hybrid"}


def nlp_trends_enabled() -> bool:
    configured = os.getenv("NLP_TREND_CLUSTERING", "auto").lower()
    if configured in {"0", "false", "off", "no", "rules"}:
        return False
    if configured in {"1", "true", "on", "yes", "embeddings"}:
        return True
    return nlp_models_enabled()


SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "ProsusAI/finbert")
ZERO_SHOT_MODEL = os.getenv("ZERO_SHOT_MODEL", "typeform/distilbert-base-uncased-mnli")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CLUSTER_DISTANCE_THRESHOLD = float(os.getenv("CLUSTER_DISTANCE_THRESHOLD", "0.42"))

CATEGORY_LABELS = [
    "macro economic and central bank news",
    "sector or industry news",
    "geopolitical and international conflict news",
    "single company or stock specific news",
]

CATEGORY_SLUGS = ["macro", "sector", "geopolitics", "single_stock"]
