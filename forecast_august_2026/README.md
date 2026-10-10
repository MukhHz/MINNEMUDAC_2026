# Question 7 August 2026 forecast

This folder contains the isolated prediction pipeline for the three statewide Minnesota food-shelf activity metrics requested in Question 7. The final forecast uses information available through July 31, 2026 only.

## Locked definitions and data policy

- **Visits:** `visits` in the prepared site-month file, derived from `HouseholdsReg`. The source's deprecated `UniqueVisits*` fields are empty.
- **Pounds distributed:** `pounds`, derived from `PoundsReg`.
- **Individuals served:** `individuals`, derived from `IndividualsReg`.
- **Source:** `Data/processed/foodshelf_site_month.csv` only. No external predictors are used.
- **Outliers:** retain all observations marked `flag_outlier` or `flag_hh_gt_indiv`. Do not trim, winsorize, or remove observations based on backtest performance.
- **Prior cleaning:** use the project's prepared file, which resolves documented blank/exact duplicates, sums distinct duplicate streams, and corrects documented impossible or clear typo values.
- **Scoring:** use MAPE provisionally, plus MAE, RMSE, median APE, and WAPE for diagnostics. Re-run selection when the official scoring rule arrives.

## Backtest design

The pipeline pretends to forecast August 2023, 2024, and 2025. Each fold trains only on records through July 31 of that year. The held-out August actual is retrieved only after every model prediction for the fold has been created.

Models:

1. `seasonal_naive`: previous August.
2. `ytd_growth`: previous August multiplied by January-July year-to-date growth.
3. `aug_jul_ratio`: current July multiplied by the median historical August/July ratio available before the cutoff.
4. `trend_month_regression`: ordinary least-squares linear trend with month-of-year indicators.
5. `robust_ensemble`: median of the four forecasts above.

A challenger replaces seasonal naive only if it has lower mean MAPE and lower August absolute percentage error in all three backtest years. This intentionally conservative rule prevents choosing a model that wins only on average because of one year.

## Run

From the project root:

```powershell
python forecast_august_2026/forecast.py
```

The script writes monthly inputs, fold-level predictions, metric summaries, final candidate forecasts, a cutoff audit, and a hashed run manifest to `forecast_august_2026/results/`.

## Advanced challenger pipeline

Run the full statistical and county-panel comparison from the `MINNEMUDAC_2026`
folder:

```powershell
python forecast_august_2026/advanced_forecasting.py
```

The advanced pipeline compares the locked baselines with ETS, constrained
SARIMA, Ridge, LASSO, Elastic Net, pooled-county LightGBM, structural ratio
forecasts, and a fixed median ensemble. It writes predictions, statewide and
county metrics, tuning history, feature diagnostics, model coefficients,
feature importance, and a run manifest to `advanced_results/`. Open
`Advanced_Forecasting_Analysis.ipynb` for the model-by-model review.

The advanced pipeline uses the newer `forecasting_pipeline/data` exports,
which exclude meal-program rows. The original isolated baseline source includes
those rows. `advanced_results/source_scope_audit.csv` records the difference so
the two target definitions are not accidentally mixed in one leaderboard.

## Complete written documentation

Start with `docs/00_INDEX.md`. The documentation set covers the executive
summary, data and preprocessing, feature engineering, every model tested,
validation and metrics, model selection, limitations, reproducibility, and all
generated artifacts.

## Cutoff guarantee

The script stops if the source contains any August 2026 or later record. For every backtest and the final run, it also asserts that the training frame ends in July of the target year. August 2026 is never loaded, merged, inferred from an external source, or used as a predictor.
