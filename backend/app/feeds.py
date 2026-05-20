from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
import http.client
import os
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


DEFAULT_RSS_SOURCES: dict[str, str] = {
    "MarketWatch": "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Google Markets": "https://news.google.com/rss/search?q=stocks%20OR%20markets%20OR%20%22S%26P%20500%22%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen",
    "Google Economy": "https://news.google.com/rss/search?q=inflation%20OR%20Fed%20OR%20rates%20OR%20Treasury%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen",
    "Google Tech": "https://news.google.com/rss/search?q=Nvidia%20OR%20Apple%20OR%20Microsoft%20OR%20AI%20stocks%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen",
    "Google Energy": "https://news.google.com/rss/search?q=oil%20OR%20crude%20OR%20OPEC%20OR%20energy%20stocks%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen",
    "Google Geopolitics": "https://news.google.com/rss/search?q=tariffs%20OR%20sanctions%20OR%20geopolitical%20markets%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen",
}

USER_AGENT = "HeadlineTrendWeb/1.0 (+local development)"
_last_fetch_report: dict[str, object] = {}


@dataclass(frozen=True)
class FeedHeadline:
    headline: str
    source: str
    timestamp: datetime
    url: str | None
    external_id: str


def configured_sources() -> dict[str, str]:
    raw_sources = os.getenv("RSS_FEED_URLS", "").strip()
    if not raw_sources:
        return DEFAULT_RSS_SOURCES

    sources: dict[str, str] = {}
    for index, item in enumerate(raw_sources.split(","), start=1):
        item = item.strip()
        if not item:
            continue
        if "=" in item:
            name, url = item.split("=", 1)
            sources[name.strip() or f"Feed {index}"] = url.strip()
        else:
            sources[f"Feed {index}"] = item
    return sources or DEFAULT_RSS_SOURCES


def fetch_feed_headlines(sources: dict[str, str] | None = None) -> list[FeedHeadline]:
    headlines: list[FeedHeadline] = []
    report: dict[str, object] = {}
    for source, url in (sources or configured_sources()).items():
        try:
            source_headlines = _fetch_source(source, url)
            headlines.extend(source_headlines)
            report[source] = {"status": "ok", "count": len(source_headlines)}
        except (OSError, ET.ParseError, http.client.IncompleteRead, urllib.error.URLError) as error:
            report[source] = {"status": "error", "error": error.__class__.__name__, "count": 0}
            continue
    global _last_fetch_report
    _last_fetch_report = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "total": len(headlines),
        "sources": report,
    }
    return headlines


def last_fetch_report() -> dict[str, object]:
    return _last_fetch_report


def _fetch_source(source: str, url: str) -> list[FeedHeadline]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=12) as response:
        body = response.read()

    root = ET.fromstring(body)
    if root.tag.endswith("feed"):
        entries = root.findall("{*}entry")
        return [_parse_atom_entry(source, entry) for entry in entries if _entry_title(entry)]

    items = root.findall(".//item")
    return [_parse_rss_item(source, item) for item in items if _entry_title(item)]


def _parse_rss_item(source: str, item: ET.Element) -> FeedHeadline:
    url = _entry_text(item, "link")
    display_source = _entry_text(item, "source") or source
    title = _strip_source_suffix(_entry_title(item), display_source)
    guid = _entry_text(item, "guid") or url or title
    timestamp = _parse_datetime(_entry_text(item, "pubDate") or _entry_text(item, "date"))
    return FeedHeadline(
        headline=title,
        source=display_source,
        timestamp=timestamp,
        url=url,
        external_id=_external_id(guid),
    )


def _parse_atom_entry(source: str, entry: ET.Element) -> FeedHeadline:
    title = _entry_title(entry)
    link = entry.find("{*}link")
    url = link.get("href") if link is not None else None
    entry_id = _entry_text(entry, "id") or url or title
    timestamp = _parse_datetime(_entry_text(entry, "updated") or _entry_text(entry, "published"))
    return FeedHeadline(
        headline=title,
        source=source,
        timestamp=timestamp,
        url=url,
        external_id=_external_id(entry_id),
    )


def _entry_text(entry: ET.Element, tag_name: str) -> str | None:
    child = entry.find(tag_name)
    if child is None:
        child = entry.find(f"{{*}}{tag_name}")
    if child is None or child.text is None:
        return None
    value = child.text.strip()
    return value or None


def _entry_title(entry: ET.Element) -> str:
    return _entry_text(entry, "title") or ""


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)

    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _external_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()


def _strip_source_suffix(title: str, source: str) -> str:
    suffix = f" - {source}"
    if title.endswith(suffix):
        return title[: -len(suffix)].strip()
    return title
