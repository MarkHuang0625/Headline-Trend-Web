from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

import pandas as pd

from src.garch_indices.config import DEFAULT_INDICES
from src.garch_indices.data import calculate_log_returns, generate_demo_prices, load_or_download_prices
from src.garch_indices.garch import fit_garch11
from src.garch_indices.reporting import (
    build_summary,
    plot_conditional_volatility,
    plot_persistence,
    write_markdown_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Fit GARCH(1,1) volatility models for global equity indices.")
    parser.add_argument("--start", default="2018-01-01", help="Start date in YYYY-MM-DD format.")
    parser.add_argument("--end", default=date.today().isoformat(), help="End date in YYYY-MM-DD format.")
    parser.add_argument("--output", default="reports", help="Directory for generated reports and charts.")
    parser.add_argument("--data-dir", default="data", help="Directory for cached Yahoo Finance CSV files.")
    parser.add_argument("--demo", action="store_true", help="Use deterministic demo data instead of Yahoo Finance.")
    parser.add_argument("--force-download", action="store_true", help="Refresh cached Yahoo Finance CSV files.")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    output_dir = Path(args.output)
    data_dir = Path(args.data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    demo_mode = args.demo
    if demo_mode:
        prices_by_index = generate_demo_prices(DEFAULT_INDICES, start, end)
    else:
        try:
            prices_by_index = load_or_download_prices(
                DEFAULT_INDICES,
                start,
                end,
                data_dir,
                force_download=args.force_download,
            )
        except Exception as exc:
            print(f"Yahoo Finance download failed: {exc}")
            print("Falling back to deterministic demo data. Re-run without network issues for real data.")
            demo_mode = True
            prices_by_index = generate_demo_prices(DEFAULT_INDICES, start, end)

    fitted = {}
    volatility_series = {}
    returns_frames = []
    for name, prices in prices_by_index.items():
        returns = calculate_log_returns(prices)
        result = fit_garch11(returns["return_pct"].to_numpy())
        returns["conditional_volatility"] = result.conditional_volatility
        fitted[name] = result
        volatility_series[name] = returns
        returns_frames.append(returns)

    summary = build_summary(fitted)
    summary.to_csv(output_dir / "summary.csv", index=False)
    pd.concat(returns_frames, ignore_index=True).to_csv(output_dir / "returns_and_volatility.csv", index=False)
    plot_conditional_volatility(volatility_series, output_dir / "conditional_volatility.png")
    plot_persistence(summary, output_dir / "persistence.png")
    write_markdown_report(summary, output_dir / "report.md", demo_mode=demo_mode)

    print(summary.to_string(index=False))
    print(f"\nReport written to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()

