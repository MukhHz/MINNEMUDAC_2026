# Multi-agent August 2026 forecasting study (Question 7)

Four specialist agents built about 100 model variants. All were scored by one shared, leakage-safe
harness (`harness.py`) under the same cutoff rules.

| Folder | Agent | Models |
|---|---|---|
| `baselines/` | — | seasonal naive, damped 3-month YoY |
| `stats/` | Statistical | AutoETS, ARIMA, Theta, CES, MSTL, YoY-ratio models, damped-YoY grid (37) |
| `panel_ml/` | Panel / many-model | per-county/site/food-bank local models + selection, global LightGBM/Ridge on YoY log-ratios (25) |
| `deep_foundation/` | DL / foundation | Chronos-Bolt, Chronos-2 zero-shot; NHITS/NBEATS/MLP trained on the county panel (17) |
| `structural/` | Structural / data quality | same-site growth, site-entry/exit models, cross-metric ratios, reporting diagnostics (22) |

## Evaluation
- **Protocol A:** forecast August 2023, 2024 and 2025, using data through July 31 of each year.
- **Protocol B:** 31 one-month-ahead forecasts, January 2024 to July 2026.
- **Cutoff checks:** asserted in `harness.make_context` for every call. Each run also writes `results/cutoff_check.txt`.
- **Rules:** `SELECTION_RULE.md` was written before any results were seen. `combine.py` applies it and writes `leaderboard_*.csv` and `final_selection.csv`.
- **Selection-bias check:** `honest_selection.py` re-runs the "pick the best models" step using only results available before each forecast date.

## Key findings
1. **July 2026 is complete.** Site counts, retention and partial-report signals are all normal. The −8% visits change vs July 2025 is real: July 2025 was a spike driven by about 10 sites.
2. **Many models beat seasonal naive in-sample.** The best were per-county model selection, MLP and NHITS on the county panel, Theta on logs, and Chronos-Bolt. Their monthly MAPE was 3.9–5% vs naive's 6.6–8.8%. Almost all of the gain comes from 2024, when the series levelled off after the ramp-up.
3. **None beats damped YoY significantly.** In paired tests over the 31 months, every p-value is above 0.3.
4. **Picking from about 100 models doesn't hold up out of sample.** In the honest replay over 2025–26, it scored 5.4–6.2% MAPE. Damped YoY scored 3.9–5.3% and seasonal naive 4.2–5.6%.
5. **August seasonality has changed.** The August/July ratio fell from 1.11–1.13 in 2022–23 to 1.03 and 0.92 in 2024–25, so July × ratio models fail.
6. **Credible models agree closely on August 2026:** visits 234k–244k, pounds 12.7M–12.9M, individuals 725k–759k.

## Outcome of this study
The study showed that no single advanced model reliably beats simple methods. It identified three robust components: seasonal naive, damped 3-month YoY and per-county local-model selection (MMF).
An earlier statewide blend of these three was superseded and removed.

**The final submitted model** is the *county-by-county selection* in `../submission/make_submission.py`. For each county it picks whichever of those components (plus their blend and the recent 3-month mean) forecast that county best over the previous 12 months.
- It lowers county WAPE from about 10.7% to **9.5% / 8.9% / 9.1%** (visits / pounds / individuals), significantly (paired Wilcoxon p = 0.036 / <0.001 / 0.006).
- See `../submission/README.md` and `../experiments/`.
