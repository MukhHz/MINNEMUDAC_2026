# External data (not used by the final Q7 model)

| File | Source | Coverage | Notes |
|---|---|---|---|
| `snap-dashboard-data-through-september-2026.xlsx` | Minnesota DHS SNAP dashboard | County/tribe, monthly, Jan 2016 – Sep 2026 | **Downloaded after the July 31, 2026 cutoff.** Used only in `forecast_august_2026/experiments/`, and only with months at least 2 (or 4) months before each forecast target. It was tested as a predictor and rejected; the submitted model does not read it. |
| `public_factors/raw/<source>/` | BLS LAUS API, Census SAIPE / PEP / CBP, CDC SVI 2022, USDA ERS food access (2019, 2025), County Health Rankings 2025 | Annual or static county / tract data, 2019–2025; **no monthly data, nothing dated 2026-08 or later** | Raw downloads cached by `notebooks/06a_build_county_factors.ipynb` (re-running reads these instead of downloading). Not used by Q7. See `docs/source_register.md`. |
| `bls_cpi/` | BLS CPI-U via Public Data API v2 (11 series: Midwest / U.S. / Minneapolis–St. Paul food at home, all items, shelter, gasoline, energy, food away) | Monthly, Jan 2019 – **Jul 2026** | **August 2026+ values were dropped in memory before saving** (the API already returns them). Used by Q4 (`notebooks/04_q4_prices_foodshelf.ipynb`), not by Q7. See `bls_cpi/README.md`. |
