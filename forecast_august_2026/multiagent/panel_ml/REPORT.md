# Panel / many-model / global-ML forecasters (MinneMUDAC 2026 Q7)

Code: `models.py` (all forecasters), `run.py` (harness run, ~2 min total), `sensitivity.py` (post-hoc diagnostics, not used to pick models).
Results: `results/summary.csv`, `results/predictions.csv`, `results/paired_vs_damped.csv`, `results/mmf_ninner_sensitivity.csv`, `results/mmf_selected_shares.txt`, `results/aggregation_check.txt`.

## Approach
* **Unit panels** built from `ctx.site` at each call (months < target only): county (86-87 units), food bank (6, `*`/`Inc.` name variants merged), site (~620 ids), site_group (5). Non-reported cells count as 0, so unit totals **sum exactly to `ctx.y`** (asserted for every level/metric at 3 cutoffs, `aggregation_check.txt`). Site entry/exit is handled inside the local rules: a unit with no last-year value gets its recent 3-month mean; a unit silent for 3 months gets 0.
* **Local many-model (bottom-up)**: per-unit seasonal naive, damped YoY (d=0.5, a priori), full YoY (d=1), recent 3m mean, recent level x last-year seasonal shape, summed to statewide.
  * `mmf_select_*` (Databricks-MMF style): per unit pick the candidate with lowest abs error over the last 6 one-step origins **inside ctx**, then sum. n_inner=6 was fixed a priori.
  * `bu_damped_tuned_*`: damping picked from {0,.25,.5,.75,1} by statewide APE on the last 12 inner origins.
* **Local ETS** (log, damped additive trend + additive seasonality, last <=36 months) per food bank / site_group. Falls back to damped YoY when there are fewer than 24 months.
* **Global models on a scale-free target** z = log(y_t / y_{t-12}) per unit (clipped to +-1), weighted by y_{t-12}. Features use only rows < t: YoY log-ratio lags 1-3, 3m/6m YoY growth, last-year month-on-month change, log level, change in the number of reporting sites, statewide z lag1 and 3m growth, month-of-year. Forecast = sum_u y_{u,t-12} * exp(zhat_u). LightGBM (fixed: 300 trees, lr .03, 8 leaves, min_child 30, seed 0) and Ridge (alpha=1, standardized, month one-hot). The `_w18` variants use only the last 18 training months. At site level (`_site_churn`) the ratio is learned on sites reporting in both years, and the statewide value is Y_{t-12} x (weighted predicted matched-site growth) x (mean churn factor of the last 3 months).
* **Ratio model** `ratio_via_visits_county`: pounds/individuals = bottom-up damped visits x damped-YoY forecast of the statewide per-visit ratio.
* **A-priori ensembles**: mean(bu_damped50_county, lgbm_county, ridge_county) and mean(bu_damped50_site, lgbm_site_churn).
* No hyperparameter was tuned against Protocol A/B. All 25 variants are reported below, losers included. Zero runtime errors.

## Results (APE in %, sorted by monthly MAPE; baselines included)

### visits

| model | aug_mape | Aug23 | Aug24 | Aug25 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| mmf_select_site | 5.15 | 8.5 | 1.3 | 5.7 | 3.48 | 4.76 | 238,204 |
| mmf_select_food_bank | 4.51 | 5.5 | 2.9 | 5.1 | 4.01 | 4.91 | 230,980 |
| mmf_select_county | 4.01 | 3.9 | 1.3 | 6.8 | 4.04 | 4.92 | 233,712 |
| global_lgbm_site_churn | 4.38 | 9.0 | 3.0 | 1.1 | 2.06 | 5.14 | 239,159 |
| ens_site_damped_lgbm | 6.09 | 11.1 | 3.9 | 3.2 | 3.56 | 5.25 | 238,498 |
| bu_damped50_county | 5.86 | 9.1 | 4.1 | 4.4 | 4.22 | 5.40 | 234,899 |
| ratio_via_visits_county | 5.86 | 9.1 | 4.1 | 4.4 | 4.22 | 5.40 | 234,899 |
| bu_damped50_food_bank | 5.34 | 8.7 | 3.8 | 3.5 | 3.66 | 5.41 | 234,171 |
| damped_yoy_3m | 5.28 | 8.6 | 3.7 | 3.6 | 3.61 | 5.43 | 234,496 |
| global_lgbm_county_w18 | 5.48 | 6.0 | 0.9 | 9.6 | 5.24 | 5.46 | 239,988 |
| global_lgbm_county | 5.03 | 6.0 | 0.9 | 8.3 | 4.57 | 5.69 | 244,593 |
| bu_damped50_site | 7.80 | 13.3 | 4.9 | 5.2 | 5.06 | 5.78 | 237,837 |
| ens_county_damped_lgbm_ridge | 6.66 | 6.4 | 5.0 | 8.6 | 6.79 | 5.88 | 239,838 |
| bu_damped_tuned_county | 4.15 | 1.1 | 7.0 | 4.4 | 5.68 | 6.06 | 237,595 |
| bu_damped_tuned_food_bank | 4.49 | 3.4 | 6.5 | 3.5 | 5.04 | 6.11 | 237,005 |
| global_lgbm_food_bank | 3.25 | 3.6 | 0.1 | 6.0 | 3.09 | 6.13 | 236,801 |
| bu_yoyfull_food_bank | 5.96 | 2.0 | 9.3 | 6.6 | 7.95 | 6.63 | 228,505 |
| bu_damped_tuned_site | 5.07 | 1.2 | 8.8 | 5.2 | 7.01 | 6.68 | 242,979 |
| bu_seasonal_level_county | 6.42 | 1.1 | 9.9 | 8.3 | 9.08 | 6.74 | 229,808 |
| bu_yoyfull_county | 6.41 | 1.1 | 9.9 | 8.3 | 9.08 | 6.75 | 229,508 |
| ets_food_bank | 11.62 | 8.7 | 12.3 | 13.9 | 13.08 | 7.04 | 249,724 |
| bu_yoyfull_site | 7.74 | 1.2 | 12.7 | 9.4 | 11.02 | 7.29 | 232,695 |
| global_ridge_site_churn | 6.52 | 2.8 | 10.2 | 6.6 | 8.40 | 7.54 | 234,405 |
| global_ridge_county | 9.07 | 4.0 | 10.1 | 13.1 | 11.58 | 7.84 | 240,022 |
| global_ridge_county_w18 | 7.39 | 4.0 | 10.1 | 8.1 | 9.07 | 7.89 | 230,510 |
| seasonal_naive | 7.20 | 19.4 | 1.8 | 0.5 | 1.12 | 8.52 | 240,290 |
| ets_site_group | 9.17 | 8.5 | 6.8 | 12.2 | 9.52 | 11.14 | 255,648 |

### pounds

| model | aug_mape | Aug23 | Aug24 | Aug25 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| mmf_select_site | 4.23 | 9.3 | 1.1 | 2.4 | 1.71 | 3.89 | 12,821,996 |
| mmf_select_county | 2.35 | 4.7 | 0.5 | 1.8 | 1.18 | 3.90 | 12,968,048 |
| mmf_select_food_bank | 1.72 | 3.3 | 0.2 | 1.7 | 0.92 | 3.94 | 12,411,401 |
| bu_damped50_site | 6.07 | 9.8 | 6.3 | 2.1 | 4.22 | 5.05 | 13,085,176 |
| ratio_via_visits_county | 5.55 | 10.2 | 5.5 | 1.0 | 3.24 | 5.13 | 12,881,171 |
| damped_yoy_3m | 5.06 | 10.1 | 5.1 | 0.0 | 2.55 | 5.16 | 12,850,522 |
| bu_damped50_food_bank | 5.06 | 10.1 | 5.1 | 0.0 | 2.56 | 5.18 | 12,860,907 |
| ens_site_damped_lgbm | 4.99 | 12.0 | 2.3 | 0.7 | 1.50 | 5.19 | 12,927,249 |
| bu_damped50_county | 5.29 | 9.7 | 5.7 | 0.4 | 3.09 | 5.20 | 12,908,092 |
| bu_damped_tuned_site | 6.37 | 5.4 | 10.4 | 3.3 | 6.84 | 5.28 | 12,908,297 |
| global_lgbm_county | 4.56 | 10.8 | 2.5 | 0.4 | 1.45 | 5.33 | 13,064,048 |
| global_lgbm_county_w18 | 4.62 | 10.8 | 2.5 | 0.6 | 1.54 | 5.41 | 12,992,626 |
| global_lgbm_food_bank | 3.63 | 3.0 | 6.9 | 1.0 | 3.94 | 5.45 | 12,872,574 |
| bu_damped_tuned_food_bank | 5.11 | 2.9 | 10.8 | 1.6 | 6.22 | 5.46 | 12,835,830 |
| bu_seasonal_level_county | 5.60 | 2.5 | 12.0 | 2.3 | 7.14 | 5.47 | 13,024,802 |
| bu_yoyfull_food_bank | 5.66 | 2.9 | 10.8 | 3.3 | 7.05 | 5.54 | 12,911,060 |
| bu_damped_tuned_county | 5.35 | 2.1 | 12.1 | 1.8 | 6.96 | 5.55 | 12,864,833 |
| bu_yoyfull_county | 5.51 | 2.1 | 12.1 | 2.3 | 7.22 | 5.58 | 12,994,610 |
| ens_county_damped_lgbm_ridge | 6.19 | 9.6 | 8.3 | 0.6 | 4.47 | 5.90 | 13,025,970 |
| bu_yoyfull_site | 5.49 | 1.1 | 14.4 | 1.0 | 7.68 | 5.92 | 13,262,056 |
| ets_food_bank | 9.86 | 10.1 | 12.2 | 7.3 | 9.77 | 6.27 | 13,214,396 |
| global_lgbm_site_churn | 6.46 | 14.2 | 1.7 | 3.5 | 2.62 | 6.31 | 12,769,322 |
| seasonal_naive | 7.03 | 17.2 | 0.6 | 3.2 | 1.92 | 6.59 | 12,821,574 |
| global_ridge_county | 8.73 | 8.5 | 16.8 | 0.9 | 8.88 | 8.14 | 13,105,769 |
| ets_site_group | 8.18 | 9.9 | 9.6 | 5.0 | 7.30 | 8.66 | 13,469,741 |
| global_ridge_site_churn | 9.34 | 11.6 | 14.7 | 1.6 | 8.18 | 9.19 | 12,813,965 |
| global_ridge_county_w18 | 10.49 | 8.5 | 16.8 | 6.2 | 11.51 | 9.35 | 12,456,302 |

### individuals

| model | aug_mape | Aug23 | Aug24 | Aug25 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| mmf_select_site | 6.49 | 10.9 | 4.8 | 3.8 | 4.31 | 4.72 | 736,542 |
| mmf_select_county | 2.92 | 5.7 | 1.7 | 1.3 | 1.55 | 4.86 | 739,204 |
| mmf_select_food_bank | 2.36 | 2.9 | 0.5 | 3.7 | 2.10 | 4.97 | 734,954 |
| ens_site_damped_lgbm | 7.35 | 14.1 | 4.9 | 3.1 | 3.99 | 5.47 | 742,220 |
| global_lgbm_site_churn | 5.61 | 11.0 | 3.5 | 2.3 | 2.90 | 5.55 | 749,978 |
| bu_damped50_site | 9.10 | 17.1 | 6.3 | 3.9 | 5.08 | 5.76 | 734,462 |
| bu_damped50_county | 7.90 | 15.0 | 5.8 | 2.9 | 4.35 | 5.79 | 725,273 |
| bu_damped50_food_bank | 7.45 | 14.8 | 5.4 | 2.1 | 3.76 | 5.83 | 724,023 |
| ratio_via_visits_county | 8.11 | 15.6 | 5.7 | 3.0 | 4.35 | 5.84 | 726,869 |
| damped_yoy_3m | 7.50 | 15.0 | 5.3 | 2.1 | 3.74 | 5.86 | 725,230 |
| ens_county_damped_lgbm_ridge | 8.00 | 9.2 | 8.2 | 6.6 | 7.41 | 6.26 | 742,197 |
| global_lgbm_county | 6.27 | 6.5 | 4.6 | 7.7 | 6.14 | 6.36 | 769,913 |
| global_lgbm_county_w18 | 6.48 | 6.5 | 4.6 | 8.3 | 6.45 | 6.39 | 782,008 |
| global_lgbm_food_bank | 5.56 | 3.5 | 10.7 | 2.4 | 6.60 | 6.44 | 775,385 |
| bu_damped_tuned_site | 6.52 | 5.1 | 10.9 | 3.6 | 7.22 | 6.45 | 739,495 |
| bu_damped_tuned_food_bank | 6.31 | 3.5 | 13.1 | 2.3 | 7.72 | 6.51 | 725,400 |
| bu_damped_tuned_county | 6.79 | 3.8 | 13.8 | 2.7 | 8.26 | 6.55 | 727,272 |
| ets_food_bank | 10.82 | 14.8 | 7.2 | 10.5 | 8.83 | 6.63 | 770,186 |
| bu_yoyfull_food_bank | 6.07 | 3.5 | 13.1 | 1.6 | 7.37 | 6.90 | 722,646 |
| bu_yoyfull_county | 6.97 | 3.8 | 13.8 | 3.3 | 8.54 | 6.98 | 723,274 |
| bu_seasonal_level_county | 6.97 | 3.8 | 13.8 | 3.3 | 8.57 | 6.99 | 724,368 |
| bu_yoyfull_site | 8.32 | 5.1 | 15.4 | 4.4 | 9.91 | 7.24 | 729,430 |
| global_ridge_county | 9.84 | 6.1 | 14.4 | 9.1 | 11.73 | 8.08 | 731,405 |
| seasonal_naive | 10.32 | 26.1 | 2.3 | 2.6 | 2.41 | 8.75 | 727,272 |
| global_ridge_county_w18 | 8.20 | 6.1 | 14.4 | 4.1 | 9.27 | 8.92 | 730,024 |
| global_ridge_site_churn | 9.40 | 6.8 | 17.0 | 4.4 | 10.70 | 9.77 | 713,807 |
| ets_site_group | 10.20 | 14.8 | 5.2 | 10.6 | 7.89 | 10.87 | 763,102 |

## Diagnostics (post hoc, `sensitivity.py`)
* **Paired vs damped_yoy_3m (31 monthly origins)**: mmf_select_county wins 16/31 (visits), 17/31 (pounds), 19/31 (indiv). Mean APE gain is 0.5 / 1.3 / 1.0 pp, with t = -0.6 / -1.5 / -1.2. That is a consistent edge but **not statistically significant**.
* **Where the gain comes from**: almost entirely 2024 (monthly MAPE 2024: mmf_county 3.9/3.3/3.8% vs damped 6.3/7.1/6.8%). That year the series plateaued after the ramp-up, and per-unit selection switched to "recent mean" (70-95% of volume selected recent_mean at Aug 2024). In 2025 it is roughly tied with damped. In **2026 it is slightly worse** (visits 7.4 vs 7.3, pounds 5.9 vs 5.3, indiv 8.3 vs 8.1). Its advantage is regime adaptivity, not better accuracy in steady state.
* **n_inner sensitivity** (3/6/12): mmf_select monthly MAPE stays 3.5-5.4% at every setting and every level, always at or below damped_yoy_3m. The result is not an artifact of n_inner=6. Aug MAPE for food_bank/visits ranges from 1.7% to 5.5%, so do not over-read the 3-fold August numbers.
* Global LightGBM on county log-ratios is now sane (5-6% monthly, vs the earlier pipeline's ~21% on levels), but it does **not** beat damped YoY. Ridge global models are clearly worse (7.8-9.8%). Ridge extrapolates the 2023 ramp-up growth relationships. ETS per unit is poor (6-11%), overfitting trend on the short ramp-up history. Inner-tuned damping is *worse* than fixed d=0.5. Its inner window chases noise.

## Nominations
| metric | nominee | aug_mape | aug 2024-25 | monthly_mape | Aug 2026 |
|---|---|---|---|---|---|
| visits | **mmf_select_county** | 4.01 | 4.04 | 4.92 | 233,712 |
| visits | (2nd) global_lgbm_site_churn | 4.38 | 2.06 | 5.14 | 239,159 |
| pounds | **mmf_select_county** | 2.35 | 1.18 | 3.90 | 12,968,050 |
| pounds | (2nd) mmf_select_food_bank | 1.72 | 0.92 | 3.94 | 12,411,400 |
| individuals | **mmf_select_county** | 2.92 | 1.55 | 4.86 | 739,204 |
| individuals | (2nd) mmf_select_site | 6.49 | 4.31 | 4.72 | 736,543 |

Reasons: one a-priori-specified method that beats both baselines on monthly MAPE and Aug MAPE for all three metrics. It is stable across levels and n_inner, cheap, and transparent (per-county choice). County is the middle granularity: the food-bank level has only 6 units, and the site level is noisy on the August folds.

## Caveats
* The edge over damped_yoy_3m is about 0.5-1.3 pp, not significant, and comes from 2024. In 2025-26 the best panel models are about tied with or slightly worse than the statewide damped YoY. A combination with the statewide baseline is a reasonable hedge.
* The Aug 2026 forecasts disagree across granularities. Pounds: 12.41M (food bank) vs 12.97M (county), a 4.5% spread. Food-bank selection picks recent_mean for 59% of volume, and May-Jul 2026 pounds ran low. Treat the spread as model uncertainty.
* Aug 2023 folds sit in the ramp-up regime and have little history (19 months), so YoY features and ETS are weak there.
* The global models use mostly 2023-25 ratios. Only 30-40 training months exist, so ML capacity is limited by history, not by units.
