from __future__ import annotations

from .config import CATEGORY_LABELS, CATEGORY_SLUGS
from .registry import zero_shot_pipeline


def classify_category_zero_shot(text: str) -> tuple[str, list[str]]:
    result = zero_shot_pipeline()(
        text[:512],
        candidate_labels=CATEGORY_LABELS,
        multi_label=False,
    )
    top_label = result["labels"][0]
    confidence = result["scores"][0]
    try:
        index = CATEGORY_LABELS.index(top_label)
    except ValueError:
        index = 0
    category = CATEGORY_SLUGS[index]
    tags = [category, f"zs_conf:{confidence:.2f}"]
    return category, tags
