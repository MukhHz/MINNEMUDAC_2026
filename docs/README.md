# Docs: in-depth explanations

Each notebook in `notebooks/` has short notes on every step. The files here explain **every decision in depth**: *what* we did, *why*, the *outcome* (with numbers) and *why not the alternatives*. Read these before presenting, so you can answer "where did this number come from?" and "why this and not that?"

| Notebook | Explainer | What it covers |
|---|---|---|
| `01_data_cleaning_mmg.ipynb` | *(to write)* | Feeding America Map the Meal Gap → MN counties 2022–2024 |
| `02_clean_foodshelf.ipynb` | [02_clean_foodshelf.md](02_clean_foodshelf.md) | Food shelf activity (`org_FSStats`) → clean site-month and county-month files + issues log |
| `03_clean_rural_share.ipynb` | *(short; notes are in the notebook)* | Census 2020 urban/rural → % rural per county |
| `01b_q1_factor_extension.ipynb` | [01b_q1_factor_extension.md](01b_q1_factor_extension.md) | Q1 extension: do 35 new public county factors (27 + 8 ACS) explain the Q1 need-vs-activity mismatch? Spearman + FDR, ≤6-predictor model, nested ΔR², LOO; child FI vs children served. Charts in `outputs/q1b/` |
| `04_q4_prices_foodshelf.ipynb` | [04_q4_prices_foodshelf.md](04_q4_prices_foodshelf.md) | Q4: grocery prices (BLS CPI) and food shelf activity: delay, all three metrics, seasons. Charts in `outputs/q4/` |
| `05_q5_snap_foodshelf.ipynb` | [05_q5_snap_foodshelf.md](05_q5_snap_foodshelf.md) (plan: [q5_plan.md](q5_plan.md)) | Q5: SNAP and food shelf use. Charts in `outputs/q5/` |
| `06a_build_county_factors.ipynb` | [source_register.md](source_register.md) (sources), [data_wishlist.md](data_wishlist.md) (what's missing) | Public county characteristics (BLS, SAIPE, Census PEP & CBP, CDC SVI, USDA food access, County Health Rankings) for Q1 and Q6 |
| `06b_acs_factors.ipynb` | [source_register.md](source_register.md) (section B2) | ACS 5-year tables via the Census API (SNAP gap, housing cost burden, foreign-born, race, seniors living alone, disability in poverty, child population), with MOEs; adds columns to `county_factors_2022_2024.csv` |
| `06c_extra_factors.ipynb` | [source_register.md](source_register.md) (section B3) | Three user-downloaded datasets: MN DEED cost of living (county, one edition), USDA SNAP retailer locator (counts 2022–2025, closures, distance to nearest full-service SNAP store), MN WIC participation (county, 2020–2022). Writes `county_extra_factors.csv` + `_static.csv`; first-look chart `outputs/q6/q6_extra_factors_first_look.png` |
| `06_q6_divergence.ipynb` | [06_q6_divergence.md](06_q6_divergence.md) | Q6: need index (8 public hardship indicators; equal weight vs PCA vs MMG), divergence from visits/pounds/individuals, stability, what explains it (incl. ACS barriers), meal-gap coverage. Charts in `outputs/q6/` |

**Start here for slides:** [00_findings_for_slides.md](00_findings_for_slides.md), one page per question with the headline numbers, charts and recommendations.

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
| `rural_share_2020_clean.csv` | county (Census 2020) | 03 |
| `cpi_monthly_2019_2026.csv` | month (BLS CPI-U, Jan 2019 – Jul 2026) | 04 |
| `county_factors_2022_2024.csv` | county × year (public factors) | 06a + 06b (ACS columns) |
| `county_factors_static.csv` | county (public factors, one vintage) | 06a |
| `county_factors_data_dictionary.csv` | one column of the `county_factors` and `county_extra_factors` files | 06a (+ 06c rows) |
| `q6_county_need_divergence.csv` | county (need index, demand, divergence, labels) | 06 (Q6) |
| `q1b_factor_tests.csv` | factor × outcome (Spearman / Kruskal-Wallis test, FDR q; 224 rows incl. 36 for the `06c` factors) | 01b |
| `county_extra_factors.csv` | county × year 2020–2025 (WIC 2020–22, SNAP retailers 2022–25) | 06c |
| `county_extra_factors_static.csv` | county (DEED cost of living, distance to SNAP stores, 2022→25 store change) | 06c |

See `Data/processed/README.md` for what's in each file. Every outside data source, and why we chose it: [source_register.md](source_register.md).
