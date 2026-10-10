# August 2026 county submission

`make_submission.py` is the single, self-contained forecasting script for the submission file.

```powershell
python forecast_august_2026/submission/make_submission.py --team-id <YourTeamID>
```

## Model
For each county, the forecast is the equal-weight mean of three local forecasts built from that county's monthly totals:

1. **Seasonal naive:** the county's August 2025 value.
2. **Damped 3-month YoY:** August 2025 × (1 + 0.5 × (May–Jul 2026 / May–Jul 2025 − 1)).
3. **MMF local selection:** per county, whichever of five simple local models had the lowest error over the six months before the cutoff.

This blend was chosen in the multi-agent study (`../multiagent/README.md`), which compared about 100 statistical, ML, deep-learning and foundation models.

## Policy
- **Columns:** `HouseholdReg_Predicted` = visits (HouseholdsReg), `PoundsReg_Predicted` = pounds (PoundsReg), `IndividualsReg_Predicted` = individuals (IndividualsReg).
- **Wilkin:** no food-shelf site appears in the data, so it is predicted as 0.
- **Cutoff:** July 31, 2026, checked in code; see `cutoff_check.txt`.

## County-level backtest (WAPE = sum of absolute county errors / sum of actuals)

| Outcome | Model | Aug 2023–25 | Monthly 2024–26 | Monthly 2026 only |
|---|---|---:|---:|---:|
| Visits | **Blend (submitted)** | 11.5% | 10.7% | 12.3% |
| Visits | MMF selection alone | 8.0% | 9.7% | 12.7% |
| Visits | Seasonal naive | 18.8% | 15.3% | 13.6% |
| Pounds | **Blend (submitted)** | 12.0% | 10.8% | 10.4% |
| Pounds | MMF selection alone | 9.8% | 9.4% | 11.1% |
| Pounds | Seasonal naive | 15.8% | 14.5% | 11.3% |
| Individuals | **Blend (submitted)** | 11.3% | 10.6% | 11.7% |
| Individuals | MMF selection alone | 6.6% | 9.4% | 12.6% |
| Individuals | Seasonal naive | 17.9% | 15.4% | 13.0% |

MMF selection alone scores better over the whole backtest, mainly because it adapted faster after the 2022–23 ramp-up. In 2026, the stable period most like August 2026, the blend beats it on all three outcomes, so the blend is submitted as the more robust choice.

## Outputs

| File | Contents |
|---|---|
| `Undergraduate_Predictions_Submit.csv` | 87 counties, ready to submit (fill in `YourTeamID`) |
| `county_forecast_components.csv` | each county's three component forecasts and the blend |
| `county_backtest_summary.csv`, `county_backtest_detail.csv` | backtest metrics |
| `cutoff_check.txt` | cutoff assertions |
| `submission_template.csv` | blank official template the script fills in |

Statewide sums of the submission: visits 236,300, pounds 12,899,236, individuals 730,575.
