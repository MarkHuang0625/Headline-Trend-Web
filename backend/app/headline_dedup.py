from __future__ import annotations

import os
import re
from difflib import SequenceMatcher

from .models import HeadlineRecord


SIMILARITY_THRESHOLD = float(os.getenv("HEADLINE_DEDUP_THRESHOLD", "0.88"))


def normalize_headline_for_dedup(text: str) -> str:
    """Normalize syndicated titles so the same story from different outlets matches."""
    lowered = text.lower().strip()
    if "|" in lowered:
        lowered = lowered.split("|", 1)[0].strip()
    lowered = re.sub(r"\s+-\s+[^-]{1,40}$", "", lowered)
    lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def headlines_are_similar(left: str, right: str, *, threshold: float = SIMILARITY_THRESHOLD) -> bool:
    normalized_left = normalize_headline_for_dedup(left)
    normalized_right = normalize_headline_for_dedup(right)
    if not normalized_left or not normalized_right:
        return False
    if normalized_left == normalized_right:
        return True
    if len(normalized_left) >= 48 and normalized_left[:48] == normalized_right[:48]:
        return True
    if abs(len(normalized_left) - len(normalized_right)) > 48:
        return False
    return SequenceMatcher(None, normalized_left, normalized_right).ratio() >= threshold


def dedupe_headlines(
    headlines: list[HeadlineRecord],
    *,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[HeadlineRecord]:
    """Keep the first (newest) headline for each near-duplicate story."""
    kept: list[HeadlineRecord] = []
    seen_exact: set[str] = set()
    prefix_buckets: dict[str, list[str]] = {}

    for headline in headlines:
        normalized = normalize_headline_for_dedup(headline.headline)
        if not normalized:
            kept.append(headline)
            continue
        if normalized in seen_exact:
            continue

        prefix = normalized[:48]
        bucket = prefix_buckets.get(prefix, [])
        if any(SequenceMatcher(None, normalized, prior).ratio() >= threshold for prior in bucket):
            continue

        kept.append(headline)
        seen_exact.add(normalized)
        bucket.append(normalized)
        prefix_buckets[prefix] = bucket

    return kept
