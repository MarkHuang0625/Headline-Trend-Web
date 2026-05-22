from app.headline_dedup import dedupe_headlines, headlines_are_similar, normalize_headline_for_dedup
from app.models import HeadlineRecord
from datetime import datetime, timezone


def test_normalize_strips_site_suffix() -> None:
    raw = "US stocks drift after oil prices rise | National News | 2news.com"
    assert "|" not in normalize_headline_for_dedup(raw)


def test_similar_syndicated_titles() -> None:
    a = "US stocks drift after oil prices rise and Nvidia's latest profit report gets a yawn"
    b = "US stocks drift after oil prices rise and Nvidia's latest profit report gets a yawn | National News | 2news.com"
    assert headlines_are_similar(a, b)


def test_dedupe_keeps_first_headline() -> None:
    now = datetime.now(timezone.utc)
    headlines = [
        HeadlineRecord(
            id=1,
            headline="US stocks drift after oil prices rise and Nvidia profit gets a yawn",
            source="A",
            timestamp=now,
            category="macro",
            sentiment="neutral",
        ),
        HeadlineRecord(
            id=2,
            headline="US stocks drift after oil prices rise and Nvidia profit gets a yawn",
            source="B",
            timestamp=now,
            category="macro",
            sentiment="neutral",
        ),
    ]
    deduped = dedupe_headlines(headlines)
    assert len(deduped) == 1
    assert deduped[0].source == "A"
