# Cleaned data

Every file here is **cleaned and ready to use**. Don't edit them by hand. If something needs changing, change the notebook and re-run it.

Full explanation of every cleaning decision: `docs/02_clean_foodshelf.md`

---

## Quick guide

| File | 1 row = | Use it for |
|---|---|---|
| `foodshelf_county_month.csv` ⭐ | 1 county, 1 month | **Most analysis**: Q1, Q4, Q5, Q7 |
| `foodshelf_site_month.csv` | 1 food shelf, 1 month | Detail about individual food shelves (maps, distance) |
| `foodshelf_issues_log.csv` | 1 data problem found | Checking what we fixed, raising issues with the organizers |
| `mmg_mn_county_2022_2024.csv` ⭐ | 1 county, 1 year | **Need** (food insecurity) for Q1 and Q6 |
| `poverty_2022_2024_clean.csv` | 1 county, 1 year | Poverty rates: explaining mismatches (Q1, Q6) |
| `vehicle_access_2022_2024_clean.csv` | 1 county, 1 year | Households without a car: access barriers (Q1, Q6) |
| `rural_share_2020_clean.csv` | 1 county | % of people living in rural areas (Q1 "rural share", Q5, Q6) |
| `snap_2022_2026_clean.csv` | 1 county **agency**, 1 month | SNAP enrollment and benefits (Q5, also Q1/Q6) |
| `snap_2022_2024_clean.csv` | 1 county agency, 1 month | Same as above, 2022–2024 only |
| `cpi_monthly_2019_2026.csv` | 1 month | Grocery and other prices (BLS CPI) and inflation, Jan 2019 – Jul 2026 (Q4) |
| `county_factors_2022_2024.csv` | 1 county, 1 year | County characteristics that change yearly (unemployment, SAIPE poverty & income, population, grocery stores; + ACS via Census API: SNAP gap, housing cost burden, foreign-born, race, seniors alone, disability in poverty): Q1 extension, Q6 |
| `county_factors_static.csv` | 1 county | County characteristics with one vintage (SVI 2022, USDA food access, County Health Rankings 2025): Q1 extension, Q6 |
| `county_factors_data_dictionary.csv` | 1 column | Definition, unit, source, vintage of every column in the two `county_factors` files and the two `county_extra_factors` files (06c rows appended) |
| `q6_county_need_divergence.csv` | 1 county | Q6 need index (equal-weight, PCA, MMG-only), demand per metric, need − demand divergence, robustness and category labels, meal-gap coverage |
| `q1b_factor_tests.csv` | 1 factor × 1 outcome | Q1 extension: does each county factor line up with the Q1 mismatch gap? ρ, p, FDR q (224 tests; `q_fdr_incl_06c` = FDR over all 224) |
| `county_extra_factors.csv` | 1 county, 1 year (2020–2025) | WIC participation (2020–2022) and SNAP-authorized retailers by store type, per 10k (1 July 2022–2025); blank = year not covered (06c) |
| `county_extra_factors_static.csv` | 1 county | MN DEED cost of living (one edition, no year), distance to nearest full-service SNAP store (2024, 2022), SNAP store openings/closings 2022→2025 (06c) |

⭐ = start here

**Metric names:**

| Name | Meaning |
|---|---|
| `visits` | household trips (from `HouseholdsReg`) |
| `pounds` | pounds of food given out |
| `individuals` | people served = adults + children + seniors |
| `fips` | official 5-digit county ID, e.g. 27053 = Hennepin. **Always join tables using this, not county names.** |

---

## 1. `foodshelf_county_month.csv` ⭐

- Food shelf activity **added up per county, per month**.
- **Every county × every month**: 87 counties × 55 months (Jan 2022 – Jul 2026) = 4,785 rows.
- Meal programs are **not** included (they serve cooked meals, a different service).
- Columns: `fips`, `county`, `month`, `visits`, `pounds`, `individuals`, `adults`, `children`, `seniors`, plus:
  - `n_sites`: how many food shelves the county had that month
  - `n_sites_reported` / `n_sites_missing`: how many sent / didn't send their numbers
- **Blank ≠ zero.** A blank means *nobody reported*, not *nobody came*.
- **Wilkin County** has `n_sites = 0` every month. It has no food shelf in the data.

---

## 2. `foodshelf_site_month.csv`

- The cleaned version of the original `org_FSStats` file: **1 food shelf, 1 month**.
- 28,101 rows, 624 food shelves.
- **Not** every food shelf has every month. A food shelf that opened in 2024 has no rows for 2022–2023.
- Includes **all** site types. Filter with `site_group`: `food_shelf`, `outreach`, `meal`, `other`, `unknown`.
- `reported = FALSE` means the food shelf existed that month but didn't send numbers.
- Flag columns (TRUE = something to know about this row):
  - `flag_dup_summed`: two rows for the same month were added together
  - `flag_typo_fixed`: an obvious typo in `visits` was removed (e.g. Waseca Jul 2023: 273,385)
  - `flag_outlier`: a value more than 10× this food shelf's usual month (kept)
  - `flag_hh_gt_indiv`: more households than people (impossible, kept but flagged)
- To drop flagged rows, filter where the flag is `FALSE`.
- `county_original` keeps the raw name (e.g. `Hennepin-Minneapolis`) if you need the city/suburb split.

---

## 3. `foodshelf_issues_log.csv`

- A **list of every problem we found** in the raw food shelf data and what we did about it: 430 rows.
- Columns: `site_id`, `year`, `month_num`, `county_original`, the **original** `visits` / `individuals` / `pounds` (before we changed anything), `issue`, `action`.
- Examples: rows removed for an impossible month (0 or 15), duplicates added together, typos set to missing.
- Use it to answer *"what happened to this number?"* and to show judges the cleaning was careful.

---

## 4. `mmg_mn_county_2022_2024.csv` ⭐

- Feeding America **Map the Meal Gap**, Minnesota only: **need** (food insecurity) per county.
- 87 counties × 3 years (2022, 2023, 2024) = 261 rows.
- Main columns:
  - `fi_rate`: % of people who are food insecure; `fi_persons`: number of food-insecure people
  - `child_fi_rate`, `fi_children`: the same for children
  - `pct_fi_above_snap_threshold`: % of food-insecure people who earn too much to get SNAP
  - `rucc_2023` / `rural`: rural-urban code (1–3 metro, 4–9 rural) / TRUE if rural
  - `source_file`: which Feeding America file the row came from
- ⚠️ `fi_rate_black`, `fi_rate_hispanic`: mostly blank (hidden for small groups). Don't rely on them.
- ⚠️ `cost_per_meal` and the budget columns **can't be compared across years** (the method changed in 2023).
- ⚠️ County numbers **don't add up** to the state total (different method). For a statewide number, use the State tab in the original file.
- Feeding America **must be cited** whenever this is used.

---

To double-check a number, open the original Excel files in `Data/ORIGINAL_MMG/` ("County" tab).

---

## 5. `poverty_2022_2024_clean.csv`

- **Poverty by county** from the US Census Bureau **American Community Survey (ACS) 5-year estimates**, table S1701.
- 87 counties × 3 years = 261 rows. Column definitions: `poverty_2022_2024_data_dictionary.csv`.
- Main columns:
  - `population`: people whose poverty status is known (a good population number for per-person rates)
  - `poverty_rate`, `poverty_count`: below the poverty line
  - `deep_poverty_rate`: income below 50% of the poverty line
  - `below_185_rate`, `below_200_rate`: below 185% / 200% of the poverty line (roughly SNAP and school-meal eligibility levels)
  - `child_poverty_rate`, `adult_poverty_rate`, `senior_60_poverty_rate`, `senior_65_poverty_rate`
- ⚠️ **`year` is the last year of a 5-year window**: `2022` = data from 2018–2022, `2024` = 2020–2024. The years overlap, so they change slowly and aren't independent.
- ⚠️ The county ID column is called **`county_geoid`** (same thing as `fips`), and county names are UPPERCASE. Join on the ID, not the name.

---

## 6. `vehicle_access_2022_2024_clean.csv`

- **Households without a car**, from the same Census ACS 5-year estimates, table B08201.
- 87 counties × 3 years = 261 rows. Column definitions: `vehicle_access_2022_2024_data_dictionary.csv`.
- Main columns:
  - `no_vehicle_rate`: % of households with **no** vehicle (`no_vehicle_households` / `total_households`)
  - `no_vehicle_rate_moe`: margin of error for that rate (90%). Small counties have bigger error.
  - `limited_vehicle_rate`: % of households with **0 or 1** vehicle
- Useful for the "can people actually get to a food shelf?" story, especially in rural counties.
- ⚠️ Same notes as poverty: `year` = end of a 5-year window, ID column is `county_geoid`, names are UPPERCASE.

---

## 7. `rural_share_2020_clean.csv`

- **% of each county's population living in rural areas**, from the US Census Bureau *2020 Census Urban and Rural* county file (original: `Data/2020_UA_COUNTY.xlsx`).
- 87 counties, one row each. Join on `fips`.
- Columns: `pop_2020`, `pop_urban_2020`, `pop_rural_2020`, **`pct_rural_2020`** (0–100), `land_sq_mi`, `pop_per_sq_mi`, `rural_band` (mostly urban <25% / mixed 25–50% / mostly rural 50–75% / rural >75%).
- **Only 2020:** the Census Bureau redraws urban/rural areas once a decade (2010 → 2020 → 2030), so this is the latest official version and covers our whole period.
- **Why use it instead of the yes/no `rural` column:** it's a percentage. 13 counties that USDA calls "metro" have **over 40% rural residents**. Fillmore is "metro" but **100% rural**, Le Sueur 86%, Mille Lacs 82%.

---

## 8. `snap_2022_2026_clean.csv` and `snap_2022_2024_clean.csv`

> 🚨 **DO NOT re-download the 2026 SNAP PDF.** The DHS page now updates every month, so a new copy may include **August 2026**, and using **any August 2026 data from any source disqualifies the team** (brief, Q7). Keep the copy we have (`Data/SNAP_2026_RAW.pdf`, which ends **March 2026**).

- **SNAP (food stamps) by month**, from the Minnesota Department of Human Services (Reports and Forecasts Division), report *"Supplemental Nutrition Assistance Program (SNAP) and State-Funded Food: Minnesota Cases, Recipients, and Payments"*: https://mn.gov/dhs/about-us/forms-resources/reports/financial-reports-and-forecasts/
- **Original PDFs:** `Data/SNAP_2022_RAW.pdf` … `Data/SNAP_2026_RAW.pdf`, one per year with one page per month by county agency. The CSV was checked against them (spot checks match exactly).
- Covers **SNAP plus Minnesota's state-funded food benefit** (for people who don't qualify for federal SNAP).
- **Publication lag:** monthly figures appear about **3 weeks** after the month ends (the 2026 PDF with data through March was created 2026-04-20). Final full-year versions come out the following January.
- `snap_2022_2026_clean.csv`: Jan 2022 – **Mar 2026**. `snap_2022_2024_clean.csv` is exactly the same data, 2022–2024 only.
- `snap_expenditure` = the PDF's **"Net Expenditure"**: benefit dollars paid that calendar month (issued minus cancelled), counted by the month paid, not the benefit month. Benefit money only, no admin costs.
- Columns: `year`, `month` (written out, e.g. `January`), `county_code`, `county`, `snap_cases` (households), `snap_people`, `snap_expenditure` (dollars of benefits).
- ⚠️ **These are 87 county *agencies*, not the 87 counties.** Some counties are combined, and tribal nations are listed separately:
  - `MNPRAIRIE` = Dodge + Steele + Waseca
  - `WPHS` = Grant + Pope
  - `MILLE-LACS-BAND TRIBE`, `WHITE EARTH NATION`, `RED LAKE INDIAN RESV`: tribal agencies, separate from their counties
- ⚠️ `county_code` is the **state's own 1–93 numbering, not FIPS**, and there's no FIPS column yet, so this **can't be joined to the other files directly**. How to match agencies to counties is still being decided.
- Benefit dollars drop sharply after **Feb 2023**, when the COVID emergency SNAP boost ended. That's a real event, not an error (useful for Q5).
- Data ends in **Mar 2026**: the state publishes with a delay of a few months.

---

## 9. `county_factors_2022_2024.csv` and `county_factors_static.csv`

- **Public-data characteristics of all 87 counties**, for explaining need-vs-food-shelf mismatches (Q1) and building the need index (Q6). They **add to** `q1_county_profiles.csv`; nothing there is repeated (poverty S1701, no-vehicle, % rural, RUCC, SNAP rate, distance, commuting are not in here).
- Every column (unit, source, vintage) is in **`county_factors_data_dictionary.csv`**. Where every source comes from and why: `docs/source_register.md`. What we couldn't get: `docs/data_wishlist.md`.
- Made by `notebooks/06a_build_county_factors.ipynb`, then **`notebooks/06b_acs_factors.ipynb` adds the ACS columns** to the yearly file (run 06a first, then 06b; 06b only adds columns). Raw downloads are in `Data/external/public_factors/raw/`.

**`county_factors_2022_2024.csv`**: 87 counties × 3 years = 261 rows. Join on `fips` + `year`.
- `pop_pep`: population on July 1 (Census estimates). Use this as the per-person denominator for a single year.
- `unemployment_rate`: % of labor force, annual average (BLS).
- `saipe_poverty_rate`, `saipe_child_poverty_rate`, `median_hh_income` (+ `_moe` = half of the 90% confidence interval): Census SAIPE **single-year** estimates. Unlike the ACS poverty file, `2023` really means 2023.
- `n_grocery_stores`, `grocery_stores_per_10k` (supermarkets & grocery, NAICS 445110), `n_food_bev_stores`, `food_bev_stores_per_10k` (all food & beverage stores, NAICS 445), from County Business Patterns.
- ⚠️ **Store counts are blank for 2024** (not released yet).
- ⚠️ **Blank store count ≠ zero.** The Census Bureau doesn't publish a count below 3, so blank (with `grocery_count_lt3 = TRUE`) means 0, 1 or 2 grocery stores. That's 17–18 small counties.
- **ACS 5-year columns (from `06b`, Census API)**, all in % (0–100) with a `_moe` (90% margin of error) column each: `pct_hh_snap`, **`pct_poverty_hh_no_snap`** (SNAP gap: poor households not on SNAP), `pct_renter_burden_30/50`, `pct_owner_burden_30/50`, `pct_hh_cost_burdened_30`, `pct_hh_severe_burden_50`, `pct_foreign_born`, `pct_noncitizen`, `pct_aian_alone`, `pct_hispanic_acs`, `pct_nonwhite`, `pct_65plus_living_alone`, `pct_disabled_in_poverty`; plus `n_poverty_hh`, `pop_under18_acs`, `acs_n_high_cv` (how many of 8 headline shares have CV > 30%) and `acs_window`.
- ⚠️ For the ACS columns, **`year` = end of a 5-year window** (2022 = 2018–22, 2024 = 2020–24), like the poverty file. `pct_aian_alone` and `pct_noncitizen` are unreliable (CV > 30%) where the share is under ~1%; the SNAP gap is unreliable only in Lake of the Woods.

**`county_factors_static.csv`**: 87 rows, one per county. Join on `fips`.
- `svi_*_pctile` and `pct_*` (uninsured, disability, limited English, single parent, mobile homes, crowding, no internet, age 65+, AIAN, …): CDC Social Vulnerability Index 2022, built from ACS **2018–2022**. Percentiles (0–1) are ranked **within Minnesota**.
- `fara_*`: USDA food access, **2019** stores (supermarkets/large grocery), 2010 population. E.g. `fara_pct_low_access_1_10` = % of people more than 1 mile (town) / 10 miles (rural) from one.
- `sram_*`: the same idea for **any store that takes SNAP**, 2025, 2020 population. Different store definition, so it doesn't match `fara_*` (correlation only 0.26).
- `pct_pop_tribal_area_approx`: rough % of people living on reservation / trust land. ⚠️ Probably undercounts Red Lake (Beltrami).
- `chr_*`: County Health Rankings **2025 release** (food environment index, severe housing cost burden, broadband, children eligible for free/reduced lunch, child care cost, social associations, census self-response, loneliness…). Each measure has its own data years; see the dictionary.
- ⚠️ Small counties (about 5,000 people or fewer: Traverse, Lake of the Woods, Red Lake, Kittson, Big Stone, Mahnomen) have large margins of error in every ACS-based number here.

---

## 10. `cpi_monthly_2019_2026.csv`

> 🚨 **Only months up to July 2026.** BLS already publishes August 2026 prices; using them disqualifies the team. They were dropped **before saving**. Never re-fetch without the same filter (see `Data/external/bls_cpi/README.md`).

- **Prices from the U.S. Bureau of Labor Statistics**, Consumer Price Index for All Urban Consumers (CPI-U). 91 months (Jan 2019 – Jul 2026), one row per month. Made by `notebooks/04_q4_prices_foodshelf.ipynb` from the cached API response in `Data/external/bls_cpi/`.
- `cpi_*` = the index as published (1982–84 = 100). Main one: **`cpi_mw_food_home`** = Midwest food at home (groceries), series `CUUR0200SAF11`. Others: U.S. food at home (`us_food_home`, `us_food_home_sa` = seasonally adjusted), Minneapolis–St. Paul food at home (`msp_food_home`), Midwest food away from home, all items (Midwest, U.S., Minneapolis–St. Paul), Midwest shelter, gasoline, energy.
- `yoy_*` = **inflation**: % change vs the same month a year earlier (blank for 2019, which has no earlier year).
- ⚠️ **October 2025 is blank** in the `cpi_*` columns (not collected during the federal shutdown). The `yoy_*` columns fill it with the midpoint of Sep and Nov 2025; `oct2025_imputed = TRUE` marks that month.
- ⚠️ `cpi_msp_all_items` is published **only in odd months** (blank otherwise).
- **Publication lag:** each month's CPI comes out around the middle of the following month.

---

## 10. `q6_county_need_divergence.csv`

- **Q6 result: where need is likely larger than food shelf activity shows.** 87 rows, one per county, sorted by `rank_underserved`. Made by `notebooks/06_q6_divergence.ipynb`; explained in `docs/06_q6_divergence.md`.
- `need_ew` (headline: equal-weight average of 8 within-year z-scores: MMG FI rate, deep poverty, income reversed, unemployment, low-income housing cost burden, disability, children in single-parent homes, uninsured <65), `need_pca`, `need_mmg`, `need_pctile`, `need_rate_adj` / `need_persons` (index on the FI-rate scale × population). **No food shelf data and no access barriers are in the need index.**
- `*_per_1k`: 2022–2024 average annual visits / pounds / individuals per 1,000 residents (complete years only where possible); `dz_*` = robust z of log activity; `dem_pctile_*`.
- `div_visits`, `div_pounds`, `div_individuals`, `div_combined`: need percentile − activity percentile (−100 to +100). **Positive = potentially underserved.** Checks: `div_z_combined`, `div_resid_combined`, `div_combined_resident` (activity reallocated to residents' county via nearest food shelf).
- `share_top15_under` / `share_top15_over`: share of 16 method versions in which the county is top 15; `category` (robust ≥ 75%); flags for small counties (<10k), Q1 data-quality, cross-county (>25% nearest shelf in another county).
- **Meal-gap coverage** (added at the end): `meal_gap_meals_2024` (MMG shortfall ÷ cost per meal), `foodshelf_meals_2024` (pounds ÷ 1.2), `meal_gap_coverage_2024` (= meals ÷ meal gap; 1.0 = 100%), `meal_gap_coverage_2023` (check), `indiv_per_fi_person_2024` (person-visits per food-insecure resident), `coverage_incomplete_2024`. Upper bound: food shelves also serve food-secure people. Don't compare with 2022 (MMG cost method changed in 2023).
- **Added from the `06c` data** (appended at the end; earlier columns unchanged): `div_combined_with_col_gap`, `need_pctile_with_col_gap` (need index with the MN DEED affordability gap as a 9th component: sensitivity), `col_affordability_gap_fam3`, `wic_infants_children_per_100_under5_2022` (validation), `snap_retailers_per_10k_2224`, `snap_full_mean_dist_mi_2024`, `snap_full_pct_over_10mi_2024`, `snap_net_change_per_10k_2022_2025` (explanations).
- ⚠️ Wilkin has need only (`category = no food shelf in data`). Divergence is **relative** (ranks among MN counties).

---

## 11. `q1b_factor_tests.csv`

- **Q1 extension result:** one row per county factor × outcome (224 rows: 46 factors + food bank region, × 4 outcomes = 188 original rows, where the 8 ACS factors are marked `batch = 06b ACS (Census API)`; then the **last 36 rows** are the 9 factors from `06c`, `batch = 06c extra (DEED / SNAP retailers / WIC)`). Made by `notebooks/01b_q1_factor_extension.ipynb`; explained in `docs/01b_q1_factor_extension.md`.
- `metric` = which Q1 gap (Method A, 2022–2024 mean): `All metrics`, `Visits`, `Pounds`, `Individuals`. Positive gap = more food shelf activity than Map the Meal Gap predicts.
- `group` = hypothesis (a. hardship, b. eligibility, c. physical access, d. awareness/stigma/social, e. network/supply, f. demographics); `is_new` = factor not used in the main Q1 notebook.
- `test` = `spearman` (`rho`) or `kruskal` (food bank region; `rho` blank). `p` = raw p-value; `q_fdr` = Benjamini–Hochberg over **all 188 tests** for the original rows (unchanged) and over all 224 for the 06c rows; `q_fdr_incl_06c` = BH over all 224 tests, every row; `q_fdr_before_acs` = the same over the first 156 tests (blank for ACS rows); `batch` = Q1 / 06a / 06b ACS; `q_fdr_within_metric` = BH within each outcome; `survives_fdr` = `q_fdr < 0.05`; `direction` = sign of rho in words.
- ⚠️ **No factor has `survives_fdr = TRUE`.** 86 counties (Wilkin has no food shelf). Associations, not causes.

---

## 12. `county_extra_factors.csv` and `county_extra_factors_static.csv`

- Made by `notebooks/06c_extra_factors.ipynb` from three files in `Data/new_extra_data/` (user downloads, read as data). Sources and why: `docs/source_register.md` section B3; every column in `county_factors_data_dictionary.csv`.
- **`county_extra_factors.csv`**: 87 counties × 2020–2025 = 522 rows. Join on `fips` + `year`.
  - `wic_*`: MN Dept. of Health WIC participants (unduplicated calendar year; total, women, infants, children 1–4), per 1,000 residents and infants + children per 100 children under 5. **2020–2022 only** (blank after).
  - `snap_*`: USDA FNS SNAP-authorized retailers active on **1 July**, all and by type (`full_service` = supermarket / super store / large grocery; `small_grocery`; `convenience`; `other`), and per 10k. **2022–2025 only** (blank before). 2025 per-10k uses 2024 population (`snap_pop_is_2024_proxy`).
- **`county_extra_factors_static.csv`**: 87 rows.
  - `col_*`: MN DEED cost of living, **one edition with no year in the file**, for a family of 3 (2 adults, 1 child, 1.5 workers) and a single adult: yearly cost, monthly food / housing / child care, required hourly wage; `col_affordability_gap_*` = yearly cost ÷ SAIPE median household income (2024; `_avg2224` = 2022–24 average).
  - `snap_full_mean_dist_mi_2024` / `_pct_over_10mi_2024` (and `_2022`), `snap_any_*_2024`: population-weighted straight-line miles from Census block groups to the nearest full-service / any SNAP store (stores in ND, SD, IA, WI included).
  - `snap_net_change_2022_2025`, `snap_closed_2022_2025`, `snap_opened_2022_2025`, `snap_full_*`, `snap_net_change_per_10k_2022_2025`, `snap_pct_change_2022_2025`: store change between 1 July 2022 and 1 July 2025.
- ⚠️ Nothing dated after December 2025 (asserted in the notebook).

---

## How to load

**Python**
```python
import pandas as pd
county = pd.read_csv("Data/processed/foodshelf_county_month.csv", dtype={"fips": str}, parse_dates=["month"])
mmg = pd.read_csv("Data/processed/mmg_mn_county_2022_2024.csv", dtype={"fips": str})
```

**R**
```r
county <- readr::read_csv("Data/processed/foodshelf_county_month.csv", col_types = readr::cols(fips = "c"))
mmg    <- readr::read_csv("Data/processed/mmg_mn_county_2022_2024.csv", col_types = readr::cols(fips = "c"))
```

Always read `fips` as **text** so `27001` stays `27001`.

To join the Census files to the others, rename their ID column:

```python
poverty = pd.read_csv("Data/processed/poverty_2022_2024_clean.csv", dtype={"county_geoid": str}).rename(columns={"county_geoid": "fips"})
```
```r
poverty <- readr::read_csv("Data/processed/poverty_2022_2024_clean.csv", col_types = readr::cols(county_geoid = "c")) |>
  dplyr::rename(fips = county_geoid)
```

**Made by:**
- `notebooks/01_data_cleaning_mmg.ipynb`: Map the Meal Gap file
- `notebooks/02_clean_foodshelf.ipynb`: food shelf files
- `notebooks/03_clean_rural_share.ipynb`: rural share file
- `notebooks/04_q4_prices_foodshelf.ipynb`: BLS price file (`cpi_monthly_2019_2026.csv`)
- `notebooks/06a_build_county_factors.ipynb`: the two `county_factors` files + dictionary
- `notebooks/06b_acs_factors.ipynb`: ACS columns (Census API) added to `county_factors_2022_2024.csv` + dictionary rows
- `notebooks/06_q6_divergence.ipynb`: `q6_county_need_divergence.csv`
- `notebooks/01b_q1_factor_extension.ipynb`: `q1b_factor_tests.csv`
- `notebooks/06c_extra_factors.ipynb`: the two `county_extra_factors` files + dictionary rows (run before 01b and 06)
- Poverty, vehicle access and SNAP files: cleaned by teammates (see each file's data dictionary / source above)
