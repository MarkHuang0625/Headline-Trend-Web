from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(".matplotlib-cache").resolve()))

import matplotlib.pyplot as plt
import pandas as pd

from .garch import GarchResult


def build_summary(results: dict[str, GarchResult]) -> pd.DataFrame:
    rows = []
    for name, result in results.items():
        rows.append(
            {
                "index": name,
                "omega": result.omega,
                "alpha_arch": result.alpha,
                "beta_garch": result.beta,
                "persistence_alpha_plus_beta": result.persistence,
                "half_life_days": result.half_life_days,
                "aic": result.aic,
                "bic": result.bic,
            }
        )
    return pd.DataFrame(rows).sort_values("persistence_alpha_plus_beta", ascending=False)


def plot_conditional_volatility(series: dict[str, pd.DataFrame], output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(12, 6))
    for name, frame in series.items():
        axis.plot(frame["date"], frame["conditional_volatility"], label=name, linewidth=1.3)
    axis.set_title("GARCH(1,1) Conditional Volatility")
    axis.set_ylabel("Daily volatility (%)")
    axis.set_xlabel("Date")
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def plot_persistence(summary: pd.DataFrame, output_path: Path) -> None:
    fig, axis = plt.subplots(figsize=(10, 5))
    axis.bar(summary["index"], summary["persistence_alpha_plus_beta"], color=["#245b86", "#d05a48", "#2d7d64", "#8a6f2a"])
    axis.axhline(1.0, color="#333333", linewidth=1, linestyle="--")
    axis.set_ylim(0, max(1.05, float(summary["persistence_alpha_plus_beta"].max()) + 0.02))
    axis.set_title("Volatility Persistence by Index")
    axis.set_ylabel("alpha + beta")
    axis.tick_params(axis="x", rotation=15)
    axis.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)


def write_markdown_report(summary: pd.DataFrame, output_path: Path, *, demo_mode: bool) -> None:
    top = summary.iloc[0]
    source_note = "deterministic demo data" if demo_mode else "Yahoo Finance adjusted close data"
    markdown = f"""# GARCH(1,1) Global Index Volatility Report

Data source: {source_note}

## Key Finding

The most persistent volatility process in this run is **{top['index']}** with alpha + beta = **{top['persistence_alpha_plus_beta']:.3f}**.

## Model

Daily log returns are modeled with:

```text
r_t = mu + epsilon_t
sigma_t^2 = omega + alpha * epsilon_(t-1)^2 + beta * sigma_(t-1)^2
```

The persistence metric is `alpha + beta`. Values close to 1 indicate volatility shocks fade slowly.

## Summary

{_markdown_table(summary)}

## Generated Charts

- `conditional_volatility.png`
- `persistence.png`
"""
    output_path.write_text(markdown, encoding="utf-8")


def _markdown_table(frame: pd.DataFrame) -> str:
    display = frame.copy()
    for column in display.columns:
        if pd.api.types.is_float_dtype(display[column]):
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{value:.4f}")

    headers = list(display.columns)
    rows = display.astype(str).values.tolist()
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)
