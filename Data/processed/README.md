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
| `MMG2025_County_MN_2022-2023_raw.csv`, `MMG2026_County_MN_2024_raw.csv` | 1 county, 1 year | Checking against the original Feeding America columns |

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

## 5. `MMG2025_County_MN_2022-2023_raw.csv` and `MMG2026_County_MN_2024_raw.csv`

- The same Map the Meal Gap data, **only filtered** (Minnesota + year). All original columns and names kept, not combined.
- Use these only to **double-check** a number against the original file. For analysis, use `mmg_mn_county_2022_2024.csv`.

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

**Made by:** `notebooks/01_data_cleaning_mmg.ipynb` (Map the Meal Gap files) and `notebooks/02_clean_foodshelf.ipynb` (food shelf files)
