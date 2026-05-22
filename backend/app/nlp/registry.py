from __future__ import annotations

from functools import lru_cache
from threading import Lock

from .config import EMBEDDING_MODEL, SENTIMENT_MODEL, ZERO_SHOT_MODEL


_load_lock = Lock()
_load_error: str | None = None


def model_load_error() -> str | None:
    return _load_error


@lru_cache(maxsize=1)
def sentiment_pipeline():
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model=SENTIMENT_MODEL,
        truncation=True,
        max_length=128,
    )


@lru_cache(maxsize=1)
def zero_shot_pipeline():
    from transformers import pipeline

    return pipeline("zero-shot-classification", model=ZERO_SHOT_MODEL)


@lru_cache(maxsize=1)
def embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def ensure_models_loaded() -> bool:
    global _load_error
    with _load_lock:
        try:
            sentiment_pipeline()
            zero_shot_pipeline()
            embedding_model()
            _load_error = None
            return True
        except Exception as exc:  # noqa: BLE001 - surface load failures to callers
            _load_error = str(exc)
            return False
