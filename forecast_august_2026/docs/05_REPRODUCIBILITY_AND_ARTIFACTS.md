# Reproducibility and Artifacts

## Main files

| File | Description |
|---|---|
| `forecast.py` | Original leakage-safe baseline pipeline |
| `advanced_forecasting.py` | Full advanced feature engineering, tuning, modeling, evaluation, selection, and export pipeline |
| `Advanced_Forecasting_Analysis.ipynb` | Executed notebook for reviewing model metrics, fold stability, forecasts, coefficients, and feature importance |
| `README.md` | Folder-level run instructions and scope notes |

## How to rerun

From the `MINNEMUDAC_2026` directory:

```powershell
python forecast_august_2026/advanced_forecasting.py
```

The script recreates `forecast_august_2026/advanced_results/`.

The full run is intentionally slower than a simple random cross-validation
workflow because the regularized models repeat chronological inner tuning for
each outer cutoff and target.

The notebook loads saved results by default. To rerun models from the notebook,
set:

```python
RUN_MODELS = True
```

## Reproducibility controls

- Random seed: 2026
- Forecast cutoff: July 31, 2026
- Backtest years: 2023, 2024, and 2025
- Target version: reported outcomes
- Primary metric: MAPE, provisional
- Primary model eligibility excludes unverified SNAP sensitivity models
- Input-file SHA-256 hashes are recorded in `run_manifest.json`
- Predictions are clipped at zero where applicable
- Hyperparameters are tuned with time-ordered folds

## Recorded software versions

| Package | Version |
|---|---:|
| Python | 3.10.12 |
| pandas | 2.3.3 |
| NumPy | 1.26.4 |
| scikit-learn | 1.7.2 |
| statsmodels | 0.14.2 |
| LightGBM | 4.6.0 |

## Generated result files

| Output | Contents |
|---|---|
| `advanced_results/RESULTS.md` | Automatically generated complete results table and selected forecasts |
| `advanced_results/statewide_backtest_predictions.csv` | Every statewide model prediction for each historical August fold |
| `advanced_results/statewide_model_summary.csv` | MAPE, median APE, MAE, RMSE, WAPE, and fold wins by model and target |
| `advanced_results/county_backtest_predictions.csv` | County-level predictions from the panel and structural models |
| `advanced_results/county_model_summary.csv` | County WAPE, MAE, RMSE, sMAPE, and median APE |
| `advanced_results/final_forecasts_all_models.csv` | August 2026 forecast from every fitted model |
| `advanced_results/selected_forecasts.csv` | The three selected hold forecasts |
| `advanced_results/tuning_history.csv` | Selected fold-specific regularization parameters and inner WAPE |
| `advanced_results/regularized_coefficients.csv` | Final Ridge, LASSO, and Elastic Net coefficients |
| `advanced_results/lightgbm_feature_importance.csv` | Final LightGBM split importance values |
| `advanced_results/feature_eligibility_audit.csv` | Primary, sensitivity-only, excluded, and prohibited feature groups |
| `advanced_results/source_scope_audit.csv` | Monthly differences between the meal-inclusive baseline source and non-meal advanced clean export |
| `advanced_results/run_manifest.json` | Cutoffs, targets, selected models, package versions, hashes, and random seed |

## Verification performed

The following automated integrity checks passed:

- Every model-target pair contained exactly three statewide backtest folds.
- Backtest years were exactly 2023, 2024, and 2025.
- Statewide actuals, forecasts, and percentage errors were finite.
- Final forecasts were finite and nonnegative.
- SNAP sensitivity models were never marked selected.
- Exactly one final model was selected for each target.
- Selected models matched the selection recorded in the run manifest.
- Every selected challenger satisfied the lower-mean-MAPE and 3/3-fold rule.
- Coefficient, LightGBM importance, county prediction, county metric, and tuning
  outputs were nonempty.
- The source audit confirmed exactly 2,702 excluded meal-program rows.
- The Python script passed syntax compilation.
- The analysis notebook was executed successfully from beginning to end with
  model rerunning disabled and saved results loaded.

## Input hashes

The run manifest records these exact inputs:

```text
food_county_month_clean.csv
145a1c02f99ba95b9150626721e8d3af9625e2ff3c74a0cf7f9f76658b2d1292

food_statewide_month_clean.csv
35d2183f4936b65853e3c3131b6caafeeef84fe35c7eeac8cb0ca8ced790105a

snap_state_month_clean.csv
8ef3847a10f8b64c3783957506ecde2a33c7ffea5b795f39f5d5e262f0d48f2a
```

## Recommended next actions

1. Confirm whether meal-program rows belong in the official target definition.
2. Confirm the official scoring metric and rerun model selection under that
   metric.
3. Verify exact SNAP, poverty, and Map the Meal Gap publication dates before
   making external variables eligible for the primary forecast.
4. Obtain additional historical monthly food-shelf data if available.
5. Reassess Ridge for pounds and LASSO for visits when another August holdout or
   longer history becomes available.
6. Keep deep learning experimental unless substantially more temporal history
   is obtained.

