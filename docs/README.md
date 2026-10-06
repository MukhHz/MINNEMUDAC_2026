# Docs: in-depth explanations

Each notebook in `notebooks/` has short notes on every step. The files here explain **every decision in depth**: *what* we did, *why*, the *outcome* (with numbers) and *why not the alternatives*. Read these before presenting, so you can answer "where did this number come from?" and "why this and not that?"

| Notebook | Explainer | What it covers |
|---|---|---|
| `01_data_cleaning_mmg.ipynb` | *(to write)* | Feeding America Map the Meal Gap → MN counties 2022–2024 |
| `02_clean_foodshelf.ipynb` | [02_clean_foodshelf.md](02_clean_foodshelf.md) | Food shelf activity (`org_FSStats`) → clean site-month and county-month files + issues log |

When a new notebook is added, add a matching `docs/NN_name.md` and a row here.

## Files produced so far (`Data/processed/`)

| File | One row = | Made by |
|---|---|---|
| `mmg_mn_county_2022_2024.csv` | county × year | 01 |
| `foodshelf_site_month.csv` | food shelf site × month | 02 |
| `foodshelf_county_month.csv` | county × month (87 × 55) | 02 |
| `foodshelf_issues_log.csv` | one data problem | 02 |
| `poverty_2022_2024_clean.csv`, `vehicle_access_2022_2024_clean.csv` | county × year (Census ACS 5-year) | teammate |
| `snap_2022_2026_clean.csv`, `snap_2022_2024_clean.csv` | county agency × month (MN DHS) | teammate |

See `Data/processed/README.md` for what's in each file.
