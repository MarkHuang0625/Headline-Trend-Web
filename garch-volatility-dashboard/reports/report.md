# GARCH(1,1) Global Index Volatility Report

Data source: deterministic demo data

## Key Finding

The most persistent volatility process in this run is **FTSE 100** with alpha + beta = **0.983**.

## Model

Daily log returns are modeled with:

```text
r_t = mu + epsilon_t
sigma_t^2 = omega + alpha * epsilon_(t-1)^2 + beta * sigma_(t-1)^2
```

The persistence metric is `alpha + beta`. Values close to 1 indicate volatility shocks fade slowly.

## Summary

| index | omega | alpha_arch | beta_garch | persistence_alpha_plus_beta | half_life_days | aic | bic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FTSE 100 | 0.0347 | 0.0562 | 0.9269 | 0.9831 | 40.6806 | 7876.4277 | 7899.3202 |
| S&P 500 | 0.0271 | 0.0526 | 0.9293 | 0.9819 | 37.8748 | 7183.3828 | 7206.2753 |
| Nikkei 225 | 0.0496 | 0.0733 | 0.9065 | 0.9799 | 34.0799 | 8212.9767 | 8235.8692 |
| EURO STOXX 50 | 0.0464 | 0.0478 | 0.9142 | 0.9620 | 17.8876 | 6816.9915 | 6839.8840 |

## Generated Charts

- `conditional_volatility.png`
- `persistence.png`

## Forecast Evaluation

Out-of-sample forecast evaluation was performed comparing Historical (rolling), EWMA (lambda=0.94) and the fitted GARCH(1,1) conditional variance. Metrics computed were RMSE, MAE and QLIKE on the hold-out sample. Across all four indices the fitted GARCH(1,1) forecasts produced the lowest RMSE/MAE/QLIKE (e.g. S&P 500: RMSE=2.3197, MAE=1.5502, QLIKE=1.4894; FTSE 100: RMSE=2.9488, MAE=1.9408, QLIKE=1.6470), indicating superior out-of-sample variance forecasting performance on this dataset. Results are saved to `reports/forecast_evaluation.csv`.
