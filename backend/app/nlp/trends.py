from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

from ..classification import tokenize
from ..models import HeadlineRecord, TrendItem, TrendPoint
from ..trends import _bucket_label, _normalize_trend_label, merge_similar_trends, trend_counts_from_buckets
from .config import CLUSTER_DISTANCE_THRESHOLD
from .registry import embedding_model


def _cluster_label(texts: list[str]) -> str:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer

    if not texts:
        return "unknown"
    if len(texts) == 1:
        tokens = tokenize(texts[0])
        return " ".join(tokens[:3]) or texts[0][:48]

    vectorizer = TfidfVectorizer(
        max_features=4,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=1,
    )
    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        tokens = tokenize(texts[0])
        return " ".join(tokens[:3]) or texts[0][:48]

    scores = np.asarray(matrix.sum(axis=0)).ravel()
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(scores, terms), reverse=True)
    label_terms = [term for score, term in ranked if score > 0][:4]
    return _normalize_trend_label(" ".join(label_terms) if label_terms else texts[0][:48])


def compute_embedding_trends(headlines: list[HeadlineRecord], *, window_hours: int) -> list[TrendItem]:
    from sklearn.cluster import AgglomerativeClustering

    if len(headlines) < 4:
        return []

    texts = [item.headline for item in headlines]
    embeddings = embedding_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    clustering = AgglomerativeClustering(
        n_clusters=None,
        distance_threshold=CLUSTER_DISTANCE_THRESHOLD,
        metric="cosine",
        linkage="average",
    )
    labels = clustering.fit_predict(embeddings)
    if len(set(labels)) == 1 and len(headlines) > 12:
        clustering = AgglomerativeClustering(n_clusters=min(8, len(headlines) // 3), metric="cosine", linkage="average")
        labels = clustering.fit_predict(embeddings)

    now = datetime.now(timezone.utc)

    cluster_texts: defaultdict[int, list[str]] = defaultdict(list)
    cluster_members: defaultdict[int, list[HeadlineRecord]] = defaultdict(list)
    cluster_mentions: defaultdict[int, list[int]] = defaultdict(list)
    cluster_series: defaultdict[int, Counter[str]] = defaultdict(Counter)

    for headline, label in zip(headlines, labels):
        cluster_texts[label].append(headline.headline)
        cluster_members[label].append(headline)
        bucket = _bucket_label(headline.timestamp, now, window_hours)
        cluster_series[label][bucket] += 1
        cluster_mentions[label].append(headline.id or 0)

    items: list[TrendItem] = []
    for label in cluster_members:
        recent_count, baseline_count = trend_counts_from_buckets(cluster_series[label])
        if recent_count < 3:
            continue
        ratio = recent_count / max(1, baseline_count)
        score = round((recent_count * 1.8) + ratio, 2)
        status = "emerging" if baseline_count == 0 or ratio >= 1.5 else "persistent"
        keyword = _cluster_label(cluster_texts[label])
        series_points = [
            TrendPoint(bucket=bucket, count=count)
            for bucket, count in sorted(cluster_series[label].items())
        ]
        items.append(
            TrendItem(
                keyword=keyword,
                recent_count=recent_count,
                baseline_count=baseline_count,
                score=score,
                status=status,
                related_headlines=cluster_mentions[label][:24],
                series=series_points,
            )
        )

    ranked = sorted(items, key=lambda item: (-item.score, -item.recent_count, item.keyword))
    return merge_similar_trends(ranked)[:10]
