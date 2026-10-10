# Question 7: August 2026 forecast

This is the isolated prediction pipeline. Information cutoff: **July 31, 2026**, enforced in code.

| Folder | Contents |
|---|---|
| `multiagent/` | Shared leakage-safe harness, the five required reference models, and 101 challenger models from four specialist agents. Also the pre-registered selection rule and the out-of-sample selection check. Start with `multiagent/README.md`. |
| `submission/` | `make_submission.py`, the final county-level model, plus its backtest and the filled `Undergraduate_Predictions_Submit.csv`. |
| `report/` | `forecasting_report.tex` / `.pdf`, the full write-up, and `make_figures.py`. |

Run everything from this folder:

```powershell
python multiagent/harness.py                         # five required reference models + damped YoY
python multiagent/combine.py                         # pooled leaderboard and selection rule
python submission/make_submission.py --team-id ID    # county forecast and submission file
python report/make_figures.py                        # report figures
```
