from __future__ import annotations

import re


STOP_WORDS = {
    "a",
    "after",
    "again",
    "as",
    "at",
    "for",
    "from",
    "into",
    "near",
    "new",
    "of",
    "on",
    "the",
    "to",
    "up",
    "with",
}

MACRO_KEYWORDS = {
    "fed",
    "inflation",
    "rates",
    "yield",
    "yields",
    "ecb",
    "boj",
    "payroll",
    "treasury",
    "auction",
    "manufacturing",
    "recession",
    "central",
    "banks",
    "policy",
    "dollar",
    "euro",
    "yen",
    "sales",
}

GEOPOLITICS_KEYWORDS = {
    "war",
    "sanctions",
    "red sea",
    "ceasefire",
    "china",
    "election",
    "shipping",
    "disruptions",
    "threats",
    "tension",
    "government",
    "governments",
}

SECTOR_KEYWORDS = {
    "tech": {"semiconductor", "ai", "cloud", "software", "cybersecurity", "server"},
    "energy": {"oil", "opec", "natural gas", "crude", "refinery", "energy"},
    "financials": {"bank", "banks", "jpmorgan", "treasury", "traders"},
    "telecom": {"telecom", "networking", "wireless"},
    "consumer": {"retail", "iphone", "delivery", "advertising"},
    "industrials": {"miners", "industrial", "shipping", "defense"},
}

TICKER_ALIASES = {
    "apple": "AAPL",
    "tesla": "TSLA",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "meta": "META",
    "amazon": "AMZN",
    "intel": "INTC",
    "jpmorgan": "JPM",
    "alphabet": "GOOGL",
    "broadcom": "AVGO",
    "exxon": "XOM",
    "chevron": "CVX",
}

POSITIVE_WORDS = {
    "beats",
    "boosts",
    "climb",
    "climbs",
    "gain",
    "gains",
    "higher",
    "improve",
    "improves",
    "outperform",
    "rally",
    "rebound",
    "strengthens",
    "surprises",
    "wins",
}

NEGATIVE_WORDS = {
    "cuts",
    "contracts",
    "cools",
    "drop",
    "drops",
    "lower",
    "miss",
    "outage",
    "pressures",
    "retreat",
    "risk",
    "slip",
    "soft",
    "stress",
    "tumbles",
    "volatility",
}


def normalize_text(text: str) -> str:
    return text.lower().strip()


def tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"[^a-zA-Z0-9\s-]", " ", normalize_text(text))
    tokens = [token for token in cleaned.split() if len(token) > 2 and token not in STOP_WORDS]
    return tokens


def extract_ticker(text: str) -> str | None:
    lowered = normalize_text(text)
    for company, ticker in TICKER_ALIASES.items():
        if company in lowered:
            return ticker

    uppercase_matches = re.findall(r"\b[A-Z]{2,5}\b", text)
    return uppercase_matches[0] if uppercase_matches else None


def classify_category(text: str) -> tuple[str, list[str]]:
    lowered = normalize_text(text)
    tags: set[str] = set()

    for phrase in GEOPOLITICS_KEYWORDS:
        if phrase in lowered:
            tags.add("geopolitics")

    macro_hits = [word for word in MACRO_KEYWORDS if word in lowered]
    if macro_hits:
        tags.update(macro_hits)

    sector_matches = []
    for sector, keywords in SECTOR_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            sector_matches.append(sector)
    tags.update(sector_matches)

    ticker = extract_ticker(text)
    if ticker:
        tags.add(ticker)
        return "single_stock", sorted(tags)

    if "geopolitics" in tags:
        return "geopolitics", sorted(tags)
    if sector_matches:
        return "sector", sorted(tags)
    if macro_hits:
        return "macro", sorted(tags)
    return "macro", sorted(tags) if tags else ["broad_market"]


def classify_sentiment(text: str) -> str:
    tokens = set(tokenize(text))
    positive_hits = len(tokens & POSITIVE_WORDS)
    negative_hits = len(tokens & NEGATIVE_WORDS)
    if positive_hits > negative_hits:
        return "positive"
    if negative_hits > positive_hits:
        return "negative"
    return "neutral"

