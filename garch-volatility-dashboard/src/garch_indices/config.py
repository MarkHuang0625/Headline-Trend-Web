from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndexConfig:
    name: str
    ticker: str


DEFAULT_INDICES: tuple[IndexConfig, ...] = (
    IndexConfig("S&P 500", "^GSPC"),
    IndexConfig("EURO STOXX 50", "^STOXX50E"),
    IndexConfig("Nikkei 225", "^N225"),
    IndexConfig("FTSE 100", "^FTSE"),
)

