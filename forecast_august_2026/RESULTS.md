# August 2026 forecast results

The conservative model-selection rule retains the previous-August seasonal naive model for visits, pounds distributed, and individuals served. No challenger produced both a lower three-year mean MAPE and a lower absolute percentage error in every backtest year.

## Rolling backtest

Mean absolute percentage error across the August 2023, 2024, and 2025 forecast folds:

| Model | Visits | Pounds | Individuals |
|---|---:|---:|---:|
| Seasonal naive | **7.20%** | 7.03% | 10.32% |
| YTD growth | 9.02% | **6.68%** | 9.79% |
| August/July ratio | 10.14% | 9.65% | 10.17% |
| Trend plus month regression | 13.06% | 10.21% | 15.49% |
| Robust median ensemble | 9.18% | 8.11% | **9.45%** |

The apparent average improvements for pounds and individuals are not stable. YTD growth beats seasonal naive in two of three pounds folds, while the robust ensemble beats it in only one of three individuals folds. Neither satisfies the locked all-three-fold consistency rule.

## Recommended hold forecast

| Metric | Selected model | Forecast before rounding | Reporting value |
|---|---|---:|---:|
| Visits | Seasonal naive | 240,290.00 | **240,290** |
| Pounds distributed | Seasonal naive | 12,821,574.42 | **12,821,574** |
| Individuals served | Seasonal naive | 727,272.00 | **727,272** |

These remain hold values rather than final submission values until the official prediction format and scoring rule arrive.

## Difference from the raw reference baseline

The prepared source produces a pounds forecast of 12,821,574.42, one pound above the raw-file value of 12,821,573.42. The difference comes from the documented cleaning rule that converts an impossible negative pounds entry to missing. Visits and individuals exactly match the raw reference baselines.

## Locked policy

- Use no record or feature dated after July 31 of the relevant forecast year.
- Use no external predictors in this pipeline.
- Use the prepared site-month file that resolves documented duplicate and clear-error records.
- Retain all 43 observations marked as high-value outliers and all 145 observations marked households-greater-than-individuals.
- Apply no clipping, winsorization, or error-driven exclusions.
- Use MAPE provisionally; re-evaluate model selection when the official scoring rule is released.
