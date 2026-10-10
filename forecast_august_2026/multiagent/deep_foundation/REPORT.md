# Deep-learning & foundation models — MinneMUDAC 2026 Q7

Code: `models.py` (all candidates), `run.py` (runs the shared harness, unchanged). Outputs: `results/predictions.csv`, `results/summary.csv`, `results/cutoff_check.txt`, `results/run_log.txt`.
Full run: Protocol A + Protocol B (31 origins) + final, all 17 variants x 3 metrics, 0 failures, 678 s on CPU.

## Models (hyperparameters fixed in advance, no tuning on harness scores, seeds fixed)
**Zero-shot foundation models** (median of the 1-step forecast; public weights from Hugging Face, never trained on this private data):
`amazon/chronos-bolt-tiny|small|base` (released Nov 2024) and `amazon/chronos-2` (released Oct 2025), via chronos-forecasting 2.3.2.
- `*_state`: statewide series; `*_state_log`: log series, then exp(median).
- `*_foodbank` / `*_county`: every food-bank (6 after merging name variants) / county (~86) series, forecast and summed (negatives clipped to 0, missing months = 0).
- `chronos2_county_xlearn`: Chronos-2 panel with `cross_learning=True`. `chronos2_multivar_log`: Chronos-2 with the 3 statewide log metrics as joint variates.

**Global neural nets** (neuralforecast 3.3.0): NHITS, generic NBEATS (identity stacks, needed for h=1), MLP (2x256). One global model per retrain covers all county x metric series (about 258), h=1, input_size=12 (lags 1..12), robust per-window scaling, MAE loss, 300 steps, lr 1e-3, start padding on, seed 1. County forecasts are summed.
**Retraining scheme (no leakage):** models are retrained at R = {1 Jan, 1 Apr, 1 Jul, 1 Aug, 1 Oct} of each year using only months < r. A target t uses the model from c = max{r in R : r <= t}, given the full history up to t-1 as input. No model is ever trained on data from month t or later. Every August fold (2023/24/25/26) uses a model retrained at that July 31 cutoff. 15 retrains per architecture.

**Ensembles (fixed in advance):** `zs_ensemble` = mean(chronos2_state_log, chronos2_county, bolt_base_state); `dl_ensemble` = mean(zs_ensemble, nhits, nbeats, mlp).

## Results (APE %, Aug 2026 forecast). Rows marked `[base]` are the reference baselines.

**visits** (sorted by monthly_mape; APE in %)

| model | aug_mape | aug23 | aug24 | aug25 | aug24-25 | monthly_mape | Aug 2026 |
|---|---|---|---|---|---|---|---|
| mlp_county | 7.00 | 13.72 | 1.27 | 6.01 | 3.64 | 4.60 | 244,927 |
| bolt_small_state | 6.72 | 12.06 | 3.10 | 5.00 | 4.05 | 4.61 | 241,227 |
| dl_ensemble | 6.72 | 13.23 | 1.00 | 5.92 | 3.46 | 4.77 | 245,008 |
| nhits_county | 6.05 | 10.16 | 1.96 | 6.04 | 4.00 | 4.81 | 247,793 |
| bolt_base_state_log | 6.13 | 12.38 | 0.92 | 5.10 | 3.01 | 4.82 | 240,272 |
| chronos2_county_xlearn | 6.63 | 11.70 | 2.64 | 5.55 | 4.09 | 4.84 | 242,993 |
| bolt_base_county | 7.11 | 12.77 | 2.57 | 5.98 | 4.27 | 4.89 | 241,243 |
| bolt_tiny_state | 7.73 | 13.95 | 2.66 | 6.58 | 4.62 | 4.90 | 243,113 |
| chronos2_county | 7.43 | 12.41 | 2.93 | 6.94 | 4.94 | 4.92 | 243,625 |
| zs_ensemble | 6.67 | 11.79 | 2.40 | 5.81 | 4.10 | 4.96 | 243,423 |
| bolt_base_state | 6.11 | 11.75 | 0.68 | 5.89 | 3.29 | 4.96 | 243,013 |
| nbeats_county | 8.24 | 17.25 | 1.64 | 5.82 | 3.73 | 5.05 | 243,889 |
| bolt_base_foodbank | 6.65 | 12.75 | 1.80 | 5.40 | 3.60 | 5.06 | 240,442 |
| chronos2_multivar_log | 6.29 | 10.79 | 3.11 | 4.97 | 4.04 | 5.10 | 243,730 |
| chronos2_state | 6.49 | 11.34 | 3.55 | 4.60 | 4.07 | 5.11 | 242,960 |
| chronos2_state_log | 6.47 | 11.22 | 3.59 | 4.59 | 4.09 | 5.15 | 243,631 |
| chronos2_foodbank | 7.24 | 11.90 | 2.71 | 7.11 | 4.91 | 5.25 | 242,452 |
| [base] damped_yoy_3m | 5.28 | 8.62 | 3.66 | 3.57 | 3.61 | 5.43 | 234,496 |
| [base] seasonal_naive | 7.20 | 19.36 | 1.75 | 0.49 | 1.12 | 8.52 | 240,290 |

**pounds** (sorted by monthly_mape; APE in %)

| model | aug_mape | aug23 | aug24 | aug25 | aug24-25 | monthly_mape | Aug 2026 |
|---|---|---|---|---|---|---|---|
| mlp_county | 4.00 | 10.20 | 0.47 | 1.34 | 0.91 | 3.96 | 12,742,317 |
| chronos2_county_xlearn | 6.17 | 14.30 | 0.29 | 3.92 | 2.10 | 4.12 | 12,905,121 |
| bolt_small_state | 5.58 | 14.95 | 1.21 | 0.59 | 0.90 | 4.15 | 12,796,079 |
| chronos2_county | 6.04 | 14.83 | 0.29 | 2.99 | 1.64 | 4.18 | 12,830,967 |
| bolt_base_state_log | 6.05 | 14.05 | 0.11 | 3.99 | 2.05 | 4.27 | 12,619,933 |
| bolt_base_foodbank | 6.11 | 14.73 | 0.31 | 3.28 | 1.80 | 4.28 | 12,804,151 |
| bolt_tiny_state | 5.96 | 15.23 | 0.91 | 1.74 | 1.32 | 4.30 | 12,819,121 |
| zs_ensemble | 5.84 | 14.04 | 0.64 | 2.83 | 1.74 | 4.32 | 12,816,325 |
| dl_ensemble | 5.18 | 12.25 | 1.53 | 1.76 | 1.64 | 4.33 | 12,791,145 |
| bolt_base_state | 5.78 | 13.76 | 0.54 | 3.04 | 1.79 | 4.33 | 12,712,250 |
| bolt_base_county | 6.81 | 15.61 | 0.68 | 4.15 | 2.41 | 4.35 | 12,760,414 |
| nhits_county | 4.50 | 11.66 | 0.04 | 1.82 | 0.93 | 4.43 | 12,876,191 |
| chronos2_foodbank | 5.74 | 13.73 | 0.09 | 3.41 | 1.75 | 4.47 | 12,841,891 |
| chronos2_multivar_log | 5.12 | 12.73 | 0.00 | 2.63 | 1.32 | 4.49 | 12,909,748 |
| chronos2_state | 6.01 | 13.35 | 2.16 | 2.52 | 2.34 | 4.63 | 12,878,525 |
| chronos2_state_log | 5.89 | 13.52 | 1.68 | 2.47 | 2.07 | 4.68 | 12,905,759 |
| nbeats_county | 6.37 | 13.09 | 4.98 | 1.04 | 3.01 | 4.78 | 12,729,746 |
| [base] damped_yoy_3m | 5.06 | 10.06 | 5.08 | 0.02 | 2.55 | 5.16 | 12,850,522 |
| [base] seasonal_naive | 7.03 | 17.25 | 0.61 | 3.23 | 1.92 | 6.59 | 12,821,574 |

**individuals** (sorted by monthly_mape; APE in %)

| model | aug_mape | aug23 | aug24 | aug25 | aug24-25 | monthly_mape | Aug 2026 |
|---|---|---|---|---|---|---|---|
| mlp_county | 6.79 | 14.59 | 1.27 | 4.50 | 2.88 | 5.11 | 758,858 |
| bolt_small_state | 6.51 | 13.08 | 2.50 | 3.94 | 3.22 | 5.19 | 738,397 |
| nhits_county | 5.17 | 10.82 | 0.50 | 4.19 | 2.34 | 5.25 | 758,783 |
| dl_ensemble | 6.32 | 13.86 | 1.05 | 4.04 | 2.54 | 5.29 | 754,260 |
| bolt_base_county | 5.49 | 13.09 | 0.41 | 2.96 | 1.69 | 5.36 | 739,416 |
| bolt_base_state_log | 4.98 | 12.67 | 0.25 | 2.02 | 1.13 | 5.44 | 725,664 |
| chronos2_county_xlearn | 5.64 | 12.44 | 0.35 | 4.13 | 2.24 | 5.44 | 753,703 |
| bolt_tiny_state | 7.08 | 14.56 | 1.46 | 5.21 | 3.33 | 5.45 | 747,760 |
| chronos2_county | 6.13 | 12.62 | 0.79 | 4.97 | 2.88 | 5.45 | 750,501 |
| nbeats_county | 8.71 | 17.98 | 4.12 | 4.03 | 4.07 | 5.46 | 752,752 |
| zs_ensemble | 5.39 | 12.05 | 0.69 | 3.43 | 2.06 | 5.54 | 746,646 |
| bolt_base_foodbank | 5.43 | 12.82 | 0.39 | 3.07 | 1.73 | 5.57 | 738,038 |
| bolt_base_state | 5.22 | 12.30 | 0.97 | 2.38 | 1.68 | 5.58 | 740,164 |
| chronos2_multivar_log | 5.46 | 11.29 | 1.90 | 3.20 | 2.55 | 5.65 | 749,090 |
| chronos2_foodbank | 5.83 | 11.49 | 1.43 | 4.56 | 2.99 | 5.71 | 745,938 |
| chronos2_state_log | 5.47 | 11.23 | 2.24 | 2.93 | 2.59 | 5.81 | 749,273 |
| chronos2_state | 5.28 | 11.11 | 2.07 | 2.64 | 2.36 | 5.81 | 749,749 |
| [base] damped_yoy_3m | 7.50 | 15.02 | 5.34 | 2.15 | 3.74 | 5.86 | 725,230 |
| [base] seasonal_naive | 10.32 | 26.15 | 2.25 | 2.56 | 2.41 | 8.75 | 727,272 |

## Findings / nominations
Thresholds come from the baselines. damped_yoy_3m: monthly 5.43/5.16/5.86, Aug 5.28/5.06/7.50, Aug24-25 3.61/2.55/3.74. seasonal_naive: Aug24-25 1.12/1.92/2.41.
- **Pounds: nominate `mlp_county`.** It beats both baselines on every summary: monthly 3.96, Aug 4.00, Aug24-25 0.91. Aug 2026 = **12,742,320 lb**. Runner-up `nhits_county`: 4.43 / 4.50 / 0.93, Aug 2026 = 12,876,190.
- **Individuals: nominate `nhits_county`.** monthly 5.25, Aug 5.17, Aug24-25 2.34. Aug 2026 = **758,783**. Alternative `bolt_base_state_log`: 5.44 / 4.98 / 1.13, Aug 2026 = 725,664.
- **Visits: no full nomination.** Every variant beats damped_yoy on monthly MAPE (best: `mlp_county` 4.60, `bolt_small_state` 4.61). But none beats damped_yoy on Aug MAPE (best: `nhits_county` 6.05 vs 5.28), and none beats seasonal_naive on Aug24-25 (1.12). The models miss Aug 2023, during the ramp-up, by 10-17%.
- All DL variants forecast Aug 2026 inside a tight band: visits 240-248k, pounds 12.6-12.9M, individuals 725-759k. Forecasts at county level and from the NNs sit about 2-4% above the statewide Chronos-Bolt forecasts.

## Caveats (please read)
- **The gains are not statistically significant.** Paired against damped_yoy_3m over the 31 monthly origins, nominated or near-nominated models win 42-58% of months, with all Wilcoxon p > 0.39. Their lower MAPE comes from fewer large misses, not from being better most months.
- **Selection bias.** The nominations are the best of 17 variants per metric, chosen after looking at scores. Expect some regression toward the baselines. Each Aug fold is a single point.
- Chronos models use a 1-step median with no covariates. With only 19-55 months of history, statewide zero-shot forecasts mostly reduce to level-plus-seasonality.
- The NNs use CPU-only, short training (300 steps) and one seed, so seed variance was not measured. NBEATS was the weakest NN.
- Retraining every quarter means monthly-origin NN forecasts use a model up to 2 months stale. That is leakage-safe but slightly handicaps the NNs.
