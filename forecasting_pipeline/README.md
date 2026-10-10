# August forecasting pipeline

This folder is the self-contained Question 7 forecasting workspace.

- Forecasting.ipynb is the fresh modeling notebook.
- data/ contains exported cleaned and model-ready CSV files.
- data/data_manifest.csv describes every export.
- CUTOFF_POLICY.md defines the historical and final information cutoffs.
- cutoff_checks.py provides executable leakage checks.

The original cleaning and diagnostic work remains in
notebooks/Forecasting.ipynb. The new notebook does not rerun that work.

Current model-ready notebook objects:

- new_statewide_foodshelf_month: reported and site-imputation-adjusted monthly
  statewide outcomes, with explicit coverage columns.
- forecast_ready_monthly: past-only food-shelf lags plus point-in-time SNAP
  features.
- model_mmg_county_year: MMG county-year features after excluding sparse and
  methodologically inconsistent fields.
- model_poverty_county_year: poverty county-year features with standardized
  FIPS.
- model_snap_state_month: statewide SNAP agency totals. SNAP must not be
  joined directly to counties without an approved allocation crosswalk.

Use the reported outcomes as the primary benchmark. Treat the imputed outcomes
as a sensitivity series until rolling August backtests demonstrate consistent
improvement.
