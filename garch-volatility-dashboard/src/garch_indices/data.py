from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from .config import IndexConfig


def fetch_yahoo_prices(index: IndexConfig, start: date, end: date) -> pd.DataFrame:
    """Download adjusted close prices from Yahoo Finance."""
    via_yfinance = _fetch_with_yfinance(index, start, end)
    if via_yfinance is not None:
        return via_yfinance
    return _fetch_with_chart_api(index, start, end)


def _fetch_with_yfinance(index: IndexConfig, start: date, end: date) -> pd.DataFrame | None:
    try:
        import yfinance as yf
    except ImportError:
        return None

    raw = yf.download(index.ticker, start=start.isoformat(), end=end.isoformat(), progress=False, auto_adjust=False)
    if raw.empty:
        raise ValueError(f"Yahoo Finance returned no prices for {index.ticker}")

    if isinstance(raw.columns, pd.MultiIndex):
        raw = raw.droplevel(-1, axis=1)
    column = "Adj Close" if "Adj Close" in raw.columns else "Close"
    frame = raw.reset_index().rename(columns={"Date": "date", column: "adj_close"})
    if isinstance(frame["adj_close"], pd.DataFrame):
        frame["adj_close"] = frame["adj_close"].iloc[:, 0]
    frame["index"] = index.name
    frame["ticker"] = index.ticker
    return frame[["date", "index", "ticker", "adj_close"]].dropna().sort_values("date").reset_index(drop=True)


def _fetch_with_chart_api(index: IndexConfig, start: date, end: date) -> pd.DataFrame:
    period1 = _unix_timestamp(start)
    period2 = _unix_timestamp(end)
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{quote(index.ticker)}"
        f"?period1={period1}&period2={period2}&interval=1d&events=history"
    )
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise ValueError(f"Yahoo Finance error for {index.ticker}: {error}")
    result = (chart.get("result") or [None])[0]
    if not result:
        raise ValueError(f"Yahoo Finance returned no prices for {index.ticker}")

    timestamps = result.get("timestamp") or []
    quote_data = (result.get("indicators", {}).get("adjclose") or result.get("indicators", {}).get("quote") or [{}])[0]
    closes = quote_data.get("adjclose") or quote_data.get("close") or []
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(timestamps, unit="s").tz_localize(None),
            "index": index.name,
            "ticker": index.ticker,
            "adj_close": closes,
        }
    )
    frame = frame[["date", "index", "ticker", "adj_close"]].dropna()
    frame = frame.sort_values("date").reset_index(drop=True)
    return frame


def load_or_download_prices(
    indices: tuple[IndexConfig, ...],
    start: date,
    end: date,
    data_dir: Path,
    *,
    force_download: bool = False,
) -> dict[str, pd.DataFrame]:
    data_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, pd.DataFrame] = {}
    for index in indices:
        cache_path = data_dir / f"{_slug(index.name)}.csv"
        if cache_path.exists() and not force_download:
            result[index.name] = _normalize_price_frame(pd.read_csv(cache_path), index)
            continue
        prices = fetch_yahoo_prices(index, start, end)
        prices.to_csv(cache_path, index=False)
        result[index.name] = prices
    return result


def generate_demo_prices(indices: tuple[IndexConfig, ...], start: date, end: date) -> dict[str, pd.DataFrame]:
    """Create deterministic GARCH-like price paths for offline smoke tests and demos."""
    dates = pd.bdate_range(start=start, end=end)
    generated: dict[str, pd.DataFrame] = {}
    seeds = {
        "S&P 500": (0.035, 0.055, 0.925, 100.0),
        "EURO STOXX 50": (0.045, 0.070, 0.900, 100.0),
        "Nikkei 225": (0.050, 0.065, 0.910, 100.0),
        "FTSE 100": (0.030, 0.050, 0.935, 100.0),
    }
    rng = np.random.default_rng(20260727)

    for index in indices:
        omega, alpha, beta, start_price = seeds[index.name]
        returns = np.zeros(len(dates))
        sigma2 = np.full(len(dates), omega / max(1.0 - alpha - beta, 0.02))
        shocks = rng.standard_normal(len(dates))
        for t in range(1, len(dates)):
            sigma2[t] = omega + alpha * returns[t - 1] ** 2 + beta * sigma2[t - 1]
            returns[t] = np.sqrt(max(sigma2[t], 1e-8)) * shocks[t]
        prices = start_price * np.exp(np.cumsum(returns / 100.0))
        generated[index.name] = pd.DataFrame(
            {
                "date": dates,
                "index": index.name,
                "ticker": index.ticker,
                "adj_close": prices,
            }
        )
    return generated


def calculate_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    frame = prices.sort_values("date").copy()
    frame["return_pct"] = np.log(frame["adj_close"]).diff() * 100.0
    return frame.dropna(subset=["return_pct"]).reset_index(drop=True)


def _normalize_price_frame(frame: pd.DataFrame, index: IndexConfig) -> pd.DataFrame:
    """Accept either project cache CSVs or raw Yahoo Finance history downloads."""
    normalized = frame.copy()
    if "date" not in normalized.columns and "Date" in normalized.columns:
        normalized = normalized.rename(columns={"Date": "date"})
    if "adj_close" not in normalized.columns:
        if "Adj Close" in normalized.columns:
            normalized = normalized.rename(columns={"Adj Close": "adj_close"})
        elif "Close" in normalized.columns:
            normalized = normalized.rename(columns={"Close": "adj_close"})

    if "date" not in normalized.columns or "adj_close" not in normalized.columns:
        raise ValueError(
            f"{index.name} cache must contain either date/adj_close or Yahoo Date/Adj Close columns."
        )

    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["index"] = index.name
    normalized["ticker"] = index.ticker
    return normalized[["date", "index", "ticker", "adj_close"]].dropna().sort_values("date").reset_index(drop=True)


def _unix_timestamp(day: date) -> int:
    return int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())


def _slug(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "_")
