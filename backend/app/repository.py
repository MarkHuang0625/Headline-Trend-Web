from __future__ import annotations

import json
import sqlite3
from threading import Lock
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .headline_dedup import dedupe_headlines, headlines_are_similar
from .nlp.pipeline import analyze_headline
from .models import HeadlineRecord
from .sample_data import build_seed_rows


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "headlines.db"


class HeadlineRepository:
    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self._lock = Lock()
        self._ensure_schema()
        self._seed_if_empty()

    def _ensure_schema(self) -> None:
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS headlines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headline TEXT NOT NULL,
                source TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                url TEXT,
                external_id TEXT,
                category TEXT NOT NULL,
                ticker TEXT,
                sentiment TEXT NOT NULL,
                tags TEXT NOT NULL
            )
            """
        )
        columns = {
            row["name"]
            for row in self.connection.execute("PRAGMA table_info(headlines)").fetchall()
        }
        if "url" not in columns:
            self.connection.execute("ALTER TABLE headlines ADD COLUMN url TEXT")
        if "external_id" not in columns:
            self.connection.execute("ALTER TABLE headlines ADD COLUMN external_id TEXT")
        self.connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_headlines_external_id "
            "ON headlines(external_id) WHERE external_id IS NOT NULL"
        )
        self.connection.commit()

    def _seed_if_empty(self) -> None:
        count = self.connection.execute("SELECT COUNT(*) AS count FROM headlines").fetchone()["count"]
        if count:
            return
        for row in build_seed_rows():
            self.insert_headline(
                headline=row["headline"],
                source=row["source"],
                timestamp=row["timestamp"],
            )

    def insert_headline(
        self,
        *,
        headline: str,
        source: str,
        timestamp: datetime | None = None,
        url: str | None = None,
        external_id: str | None = None,
    ) -> HeadlineRecord:
        analysis = analyze_headline(headline)
        category = analysis.category
        tags = analysis.tags
        ticker = analysis.ticker
        sentiment = analysis.sentiment
        resolved_timestamp = (timestamp or datetime.now(timezone.utc)).astimezone(timezone.utc)

        with self._lock:
            if external_id:
                existing = self.connection.execute(
                    "SELECT * FROM headlines WHERE external_id = ?",
                    (external_id,),
                ).fetchone()
                if existing:
                    return self._row_to_record(existing)
            if url:
                existing = self.connection.execute(
                    "SELECT * FROM headlines WHERE url = ?",
                    (url,),
                ).fetchone()
                if existing:
                    return self._row_to_record(existing)

            similar = self._find_similar_headline(headline, resolved_timestamp)
            if similar:
                return similar

            cursor = self.connection.execute(
                """
                INSERT INTO headlines
                    (headline, source, timestamp, url, external_id, category, ticker, sentiment, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    headline,
                    source,
                    resolved_timestamp.isoformat(),
                    url,
                    external_id,
                    category,
                    ticker,
                    sentiment,
                    json.dumps(tags),
                ),
            )
            self.connection.commit()
            row = self.connection.execute("SELECT * FROM headlines WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return self._row_to_record(row)

    def get_by_id(self, headline_id: int) -> HeadlineRecord:
        with self._lock:
            row = self.connection.execute("SELECT * FROM headlines WHERE id = ?", (headline_id,)).fetchone()
        return self._row_to_record(row)

    def list_headlines(
        self,
        *,
        search: str | None = None,
        category: str | None = None,
        ticker: str | None = None,
        hours: int = 24,
        limit: int = 100,
    ) -> list[HeadlineRecord]:
        query = "SELECT * FROM headlines WHERE timestamp >= ?"
        params: list[object] = [(datetime.now(timezone.utc)).isoformat()]
        window_start = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        params[0] = datetime.fromtimestamp(window_start, tz=timezone.utc).isoformat()

        if search:
            query += " AND lower(headline) LIKE ?"
            params.append(f"%{search.lower()}%")
        if category and category != "all":
            query += " AND category = ?"
            params.append(category)
        if ticker:
            query += " AND ticker = ?"
            params.append(ticker.upper())

        fetch_limit = min(limit * 4, 2000)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(fetch_limit)

        with self._lock:
            rows = self.connection.execute(query, tuple(params)).fetchall()
        records = [self._row_to_record(row) for row in rows]
        return dedupe_headlines(records)[:limit]

    def all_headlines(self, *, hours: int = 24) -> list[HeadlineRecord]:
        window_start = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        with self._lock:
            rows = self.connection.execute(
                "SELECT * FROM headlines WHERE timestamp >= ? ORDER BY timestamp ASC",
                (datetime.fromtimestamp(window_start, tz=timezone.utc).isoformat(),),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def available_tickers(self) -> list[str]:
        with self._lock:
            rows = self.connection.execute(
                "SELECT DISTINCT ticker FROM headlines WHERE ticker IS NOT NULL ORDER BY ticker ASC"
            ).fetchall()
        return [row["ticker"] for row in rows]

    def _find_similar_headline(self, headline: str, timestamp: datetime) -> HeadlineRecord | None:
        window_start = timestamp - timedelta(hours=72)
        with self._lock:
            rows = self.connection.execute(
                """
                SELECT * FROM headlines
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
                LIMIT 300
                """,
                (window_start.isoformat(),),
            ).fetchall()

        for row in rows:
            record = self._row_to_record(row)
            if headlines_are_similar(headline, record.headline):
                return record
        return None

    def _row_to_record(self, row: sqlite3.Row) -> HeadlineRecord:
        return HeadlineRecord(
            id=row["id"],
            headline=row["headline"],
            source=row["source"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            url=row["url"],
            category=row["category"],
            ticker=row["ticker"],
            sentiment=row["sentiment"],
            tags=json.loads(row["tags"]),
        )
