#!/usr/bin/env python3
"""Out-of-sample volatility forecast evaluation.

Produces RMSE, MAE, and QLIKE for Historical (rolling), EWMA, and GARCH(1,1)
forecasts using data in reports/returns_and_volatility.csv.
"""
import math
from pathlib import Path
import pandas as pd
import numpy as np


def qlike(realized, forecast):
    # QLIKE = mean( realized / forecast + log(forecast) )
    # add tiny epsilon to avoid division by zero / log(0)
    eps = 1e-10
    f = np.maximum(forecast, eps)
    r = np.maximum(realized, 0.0)
    return float(np.mean(r / f + np.log(f)))


def evaluate_index(df, window=20, ewma_lambda=0.94, test_frac=0.2):
    # df must contain columns: 'date','return_pct','conditional_volatility'
    df = df.sort_values('date').reset_index(drop=True)
    realized = (df['return_pct'].astype(float) ** 2).values
    cond_vol = df['conditional_volatility'].astype(float).values

    n = len(df)
    split = int((1 - test_frac) * n)
    if split < window + 5:
        # not enough data
        return None

    # Precompute shifted GARCH forecast: use last available conditional_volatility (sigma_t)
    # as forecast for next-day variance, so shift by 1
    garch_forecast_series = np.roll(cond_vol, 1) ** 2
    garch_forecast_series[0] = cond_vol[0] ** 2

    hist_forecasts = []
    ewma_forecasts = []
    garch_forecasts = []
    reals = []

    # initialize ewma with training data
    train_realized = realized[:split]
    if len(train_realized) < 1:
        return None
    # use pandas ewm to get last value
    ewma_init = pd.Series(train_realized).ewm(alpha=1 - ewma_lambda, adjust=False).mean().iloc[-1]

    ewma = float(ewma_init)

    # rolling evaluation: for each day t in test set, forecast using data up to t-1
    for i in range(split, n):
        # history window last `window` realized values up to i-1
        start = max(0, i - window)
        hist_var = float(np.mean(realized[start:i])) if i - start > 0 else float(np.mean(train_realized[-window:]))

        hist_forecasts.append(hist_var)
        ewma_forecasts.append(ewma)
        garch_forecasts.append(float(garch_forecast_series[i]))

        reals.append(float(realized[i]))

        # update ewma with realized at i (so it's ready for next step)
        ewma = ewma_lambda * ewma + (1 - ewma_lambda) * float(realized[i])

    reals = np.array(reals)
    hist_forecasts = np.array(hist_forecasts)
    ewma_forecasts = np.array(ewma_forecasts)
    garch_forecasts = np.array(garch_forecasts)

    # metrics
    def rmse(a, b):
        return float(np.sqrt(np.mean((a - b) ** 2)))

    def mae(a, b):
        return float(np.mean(np.abs(a - b)))

    results = {
        'Historical': {
            'RMSE': rmse(reals, hist_forecasts),
            'MAE': mae(reals, hist_forecasts),
            'QLIKE': qlike(reals, hist_forecasts),
        },
        'EWMA': {
            'RMSE': rmse(reals, ewma_forecasts),
            'MAE': mae(reals, ewma_forecasts),
            'QLIKE': qlike(reals, ewma_forecasts),
        },
        'GARCH(1,1)': {
            'RMSE': rmse(reals, garch_forecasts),
            'MAE': mae(reals, garch_forecasts),
            'QLIKE': qlike(reals, garch_forecasts),
        },
    }

    return results


def main():
    repo_root = Path(__file__).resolve().parents[2]
    data_path = repo_root / 'reports' / 'returns_and_volatility.csv'
    out_path = repo_root / 'reports' / 'forecast_evaluation.csv'

    df = pd.read_csv(data_path, parse_dates=['date'])

    rows = []
    for idx, sub in df.groupby('index'):
        res = evaluate_index(sub)
        if res is None:
            continue
        for method, metrics in res.items():
            rows.append({
                'index': idx,
                'method': method,
                'RMSE': metrics['RMSE'],
                'MAE': metrics['MAE'],
                'QLIKE': metrics['QLIKE'],
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(out_path, index=False)
    print(f'Wrote forecast evaluation to {out_path}')


if __name__ == '__main__':
    main()
