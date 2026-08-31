# GARCH Model for Global Indices

This project estimates GARCH(1,1) volatility models for four major global equity indices and compares volatility persistence across markets.

## Indices

| Index | Yahoo Finance ticker |
| --- | --- |
| S&P 500 | `^GSPC` |
| EURO STOXX 50 | `^STOXX50E` |
| Nikkei 225 | `^N225` |
| FTSE 100 | `^FTSE` |

## What It Does

- Downloads daily adjusted close prices from Yahoo Finance.
- Computes daily log returns.
- Fits a Gaussian GARCH(1,1) model for each index.
- Reports `omega`, ARCH `alpha`, GARCH `beta`, AIC, BIC, and volatility persistence `alpha + beta`.
- Generates comparison charts and CSV outputs.
- Falls back to deterministic demo data if Yahoo Finance is unavailable.

## Project Structure

```text
garch-volatility-dashboard/
├── README.md
├── requirements.txt
├── run_analysis.py
├── data/
│   └── .gitkeep
├── reports/
│   └── .gitkeep
├── tests/
│   └── test_garch_workflow.py
└── src/
    └── garch_indices/
        ├── __init__.py
        ├── config.py
        ├── data.py
        ├── garch.py
        └── reporting.py
```

## Quick Start

```bash
cd garch-volatility-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run_analysis.py
```

For the most reliable live Yahoo Finance download path, install the optional Yahoo helper:

```bash
pip install -r requirements-yahoo.txt
```

Outputs are written to `reports/`:

- `summary.csv`
- `returns_and_volatility.csv`
- `conditional_volatility.png`
- `persistence.png`
- `report.md`

## Offline Demo

Use demo mode when you want to verify the whole workflow without internet access:

```bash
python run_analysis.py --demo
```

## Tests

```bash
python -m unittest
```

## Example Options

```bash
python run_analysis.py --start 2020-01-01 --end 2026-07-27 --force-download
```

## Manual Yahoo CSV Download

If your browser can access Yahoo Finance but the terminal cannot, download CSV files manually from Yahoo Finance Historical Data and place them in `data/` with these names:

| Index | Yahoo Finance page | Save as |
| --- | --- | --- |
| S&P 500 | `https://finance.yahoo.com/quote/%5EGSPC/history/` | `data/sandp_500.csv` |
| EURO STOXX 50 | `https://finance.yahoo.com/quote/%5ESTOXX50E/history/` | `data/euro_stoxx_50.csv` |
| Nikkei 225 | `https://finance.yahoo.com/quote/%5EN225/history/` | `data/nikkei_225.csv` |
| FTSE 100 | `https://finance.yahoo.com/quote/%5EFTSE/history/` | `data/ftse_100.csv` |

Then run without `--force-download`:

```bash
python run_analysis.py
```

The script accepts raw Yahoo CSV columns such as `Date`, `Close`, and `Adj Close`.

## Theory Notes

The project models daily returns as:

```text
r_t = mu + epsilon_t
sigma_t^2 = omega + alpha * epsilon_(t-1)^2 + beta * sigma_(t-1)^2
```

`alpha` captures short-term shock sensitivity, `beta` captures volatility persistence, and `alpha + beta` is the main persistence comparison metric. Values close to 1 mean volatility shocks decay slowly.
