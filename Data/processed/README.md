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
| `snap_2022_2026_clean.csv` | 1 county **agency**, 1 month | SNAP enrollment and benefits (Q5, also Q1/Q6) |
| `snap_2022_2024_clean.csv` | 1 county agency, 1 month | Same as above, 2022–2024 only |

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

## 7. `snap_2022_2026_clean.csv` and `snap_2022_2024_clean.csv`

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
- Poverty, vehicle access and SNAP files: cleaned by teammates (see each file's data dictionary / source above)
