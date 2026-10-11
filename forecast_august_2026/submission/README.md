# August 2026 county submission

`make_submission.py` is the single, self-contained forecasting script for the submission file.

```powershell
python forecast_august_2026/submission/make_submission.py --team-id <YourTeamID>
```

## Final model: county-by-county selection
Each county uses whichever of five candidate forecasts had the lowest absolute error on **that county** over the 12 one-month-ahead forecasts before the cutoff:

| Candidate | Definition |
|---|---|
| Seasonal naive | the county's August 2025 value |
| Damped 3-month YoY | August 2025 × (1 + 0.5 × (May–Jul 2026 / May–Jul 2025 − 1)) |
| MMF local selection | whichever of five simple local models had the lowest error over the last 6 months |
| Blend | equal-weight mean of the three above (the earlier submission, chosen in `../multiagent`) |
| Recent 3-month mean | May–Jul 2026 average |

If a county has too little history to score all 12 origins, the blend is used. This happens in the August 2023 backtest fold.

For August 2026, the visits forecasts used the recent mean in 33 counties, damped YoY in 21, the blend in 14, seasonal naive in 10 and MMF in 8.
Counties with a recent level shift move to the recent mean. For example, Mille Lacs gained a new site in April 2026, so its forecast is 1,550 visits instead of the blend's 991.

## Why this model (county-level backtest, 31 monthly origins Jan 2024 – Jul 2026)

| Metric | Visits: blend → final | Pounds: blend → final | Individuals: blend → final |
|---|---|---|---|
| WAPE | 10.67% → **9.51%** | 10.75% → **8.91%** | 10.64% → **9.13%** |
| County MAPE | 15.37% → **13.62%** | 20.28% → **17.36%** | 15.46% → **13.76%** |
| RMSE | 1,057 → **970** | 46,939 → **39,524** | 3,222 → **2,775** |
| Bias | −3.0% → **−0.5%** | −1.2% → **+0.1%** | −2.7% → **+0.1%** |
| Statewide APE | 5.51% → **4.79%** | 4.72% → **3.71%** | 5.74% → **4.73%** |

- **Paired test:** the final model beats the blend in 21/31, 24/31 and 19/31 months. Wilcoxon p = 0.036, <0.001 and 0.006.
- **Caveat:** it was chosen from four county-tailoring variants after looking at the results. After correcting for that, pounds and individuals remain significant and visits is borderline.

August folds, county WAPE (%), blend → final:

| Outcome | 2023 | 2024 | 2025 |
|---|---|---|---|
| Visits | 20.7 → 20.7 | 7.4 → 8.0 | 6.6 → 6.1 |
| Pounds | 14.3 → 14.3 | 10.2 → 7.9 | 11.5 → 10.5 |
| Individuals | 20.3 → 20.3 | 7.5 → 8.1 | 6.2 → 4.1 |

Full metrics are in `county_backtest_summary.csv`, with columns `final`, `blend`, `seasonal_naive`, `damped_yoy_3m` and `mmf_select`.

## Policy
- **Columns:** `HouseholdReg_Predicted` = visits (HouseholdsReg), `PoundsReg_Predicted` = pounds (PoundsReg), `IndividualsReg_Predicted` = individuals (IndividualsReg).
- **Wilkin:** no food-shelf site appears in the data, so it is predicted as 0.
- **Cutoff:** July 31, 2026, checked in code; see `cutoff_check.txt`. The 12 selection origins all lie before each target month.

## Outputs

| File | Contents |
|---|---|
| `Undergraduate_Predictions_Submit.csv` | 87 counties, ready to submit (fill in `YourTeamID`) |
| `county_forecast_components.csv` | every candidate forecast per county, the final value and the chosen candidate |
| `county_backtest_summary.csv`, `county_backtest_detail.csv` | backtest metrics |
| `cutoff_check.txt` | cutoff assertions |
| `submission_template.csv` | blank official template the script fills in |

Statewide sums of the submission: **visits 237,861, pounds 12,994,439, individuals 738,532**.
Empirical 80% ranges from the monthly backtest: visits 221k–258k, pounds 12.19M–13.62M, individuals 697k–802k.
