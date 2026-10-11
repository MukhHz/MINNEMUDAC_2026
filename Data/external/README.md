# External data (not used by the final Q7 model)

| File | Source | Coverage | Notes |
|---|---|---|---|
| `snap-dashboard-data-through-september-2026.xlsx` | Minnesota DHS SNAP dashboard | County/tribe, monthly, Jan 2016 – Sep 2026 | **Downloaded after the July 31, 2026 cutoff.** Used only in `forecast_august_2026/experiments/`, and only with months at least 2 (or 4) months before each forecast target. It was tested as a predictor and rejected; the submitted model does not read it. |
