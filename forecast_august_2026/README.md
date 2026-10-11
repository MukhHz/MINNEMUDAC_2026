# Question 7: August 2026 forecast

This is the isolated prediction pipeline. Information cutoff: **July 31, 2026**, enforced in code.

**Final model:** county-by-county selection (`submission/make_submission.py`). Each county uses whichever of five robust forecasts tracked it best over the previous 12 months: seasonal naive, damped YoY, local-model selection, their blend, or the recent 3-month mean.
- County WAPE is 9.5% / 8.9% / 9.1% (visits / pounds / individuals), about 40% below seasonal naive.
- Statewide totals: **237,861 visits, 12,994,439 lb, 738,532 individuals**.

| Folder | Contents |
|---|---|
| `submission/` | **The final model**, its county backtest and the filled `Undergraduate_Predictions_Submit.csv`. |
| `multiagent/` | Shared leakage-safe harness, the five required Q7 reference models, and 101 challenger models (statistical, panel ML, deep learning/foundation, structural). Also the selection rule and the out-of-sample selection check. |
| `experiments/` | The county-tailoring comparison that chose the final model, and the external predictors (SNAP, calls) that were tested and rejected. |
| `report/` | `forecasting_report.tex` / `.pdf` (full write-up) and `make_figures.py`. |

Run from this folder:

```powershell
python submission/make_submission.py --team-id ID    # final county forecast and submission file
python multiagent/harness.py                         # five required reference models + damped YoY
python multiagent/combine.py                         # pooled leaderboard of the 101-model study
python experiments/county_tailoring.py               # how the final model was chosen
python experiments/external_predictors.py            # SNAP / calls predictor tests
python report/make_figures.py                        # report figures
```
