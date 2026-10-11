# Experiments behind the final model

These scripts document the tests run after the multi-agent study. Run them from `forecast_august_2026/`; outputs go to `results/`.

## `county_tailoring.py`: how the final model was chosen
County-level backtest (31 monthly origins Jan 2024 – Jul 2026, plus the August folds) of four ways to tailor forecasts to counties:

| Variant | Monthly county WAPE, visits / pounds / individuals |
|---|---|
| A. Same blend for every county | 10.67 / 10.75 / 10.64 |
| B. Site-level blend summed to counties | 10.3 / 11.5 / 10.2 |
| C. B with one-off spikes capped | 10.4 / 11.5 / 10.3 |
| **D. County-by-county selection (final)** | **9.51 / 8.91 / 9.13** |

D beats A in 21, 24 and 19 of 31 months (Wilcoxon p = 0.036, <0.001, 0.006).
The full metric set (MAPE, MdAPE, MAE, RMSE, bias, error relative to naive, statewide APE) is in `results/county_tailoring_metrics_monthly.csv`.

## `external_predictors.py`: predictors tested and rejected

| Predictor | Lag used | Result |
|---|---|---|
| MN county SNAP enrolment (`Data/processed/snap_2022_2026_clean.csv`) | 5 months | No gain; as a selection candidate it won in about half the months (p ≈ 0.8) |
| MN DHS SNAP dashboard: persons, inverse persons, inverse benefit per person (`Data/external/`) | 2 and 4 months | No gain; pounds significantly *worse* at lag 2 (p = 0.014) |
| Incoming calls (`Data/Incoming Call.xlsx`), statewide, effect fitted on past data only | 2 months | Worse than damped YoY (MAPE 5.6 / 5.5 / 6.2% vs 5.4 / 3.7 / 5.5%) |

SNAP ratio forecasts were worse than plain seasonal naive.
**Why they fail:** these predictors move slowly (a few percent a year), while county food-shelf changes are driven by site-level events (openings, one-off spikes, reporting changes).

**Not tested as a predictor:** national USDA SNAP totals (`snap-4fymonthly`). They are national only, and that file was published on September 11, 2026, after the cutoff. Context: national SNAP participation fell about 13% year over year by June 2026, while Minnesota food-shelf visits stayed flat. This is noted in the report as a risk.

## Cutoff
- Every forecast for month *t* uses predictor values dated at least the stated lag before *t*.
- The SNAP dashboard is truncated to months ≤ July 2026 before use.
- None of these predictors is read by `submission/make_submission.py`.
