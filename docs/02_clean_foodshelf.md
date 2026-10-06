# 02 · Cleaning the food shelf data (`org_FSStats`), explained

Companion to `notebooks/02_clean_foodshelf.ipynb`. The notebook has short notes. This file explains **every decision in depth**: what we did, why, what changed, and why we didn't do something else. Use it to prepare for judge questions like *"where did this number come from?"* and *"why this and not that?"*

---

## The big picture

`org_FSStats.xlsx` is The Food Group's master record of food shelf activity: **one row per food shelf site per month**, Jan 2022 – Jul 2026, 28,287 rows. It's raw operational data typed in by hundreds of sites, so it has typos, duplicates, inconsistent county names and gaps.

We clean it **once** so every question (Q1, Q4, Q5, Q6, Q7) starts from the same numbers.

| Output (`Data/processed/`) | One row = | Used for |
|---|---|---|
| `foodshelf_site_month.csv` | one site, one month (28,101 rows) | the master file; anything needing site detail (maps, distance) |
| `foodshelf_county_month.csv` | one county, one month (87 × 55 = 4,785 rows) | Q1 (summed to years), Q4, Q5, Q7 |
| `foodshelf_issues_log.csv` | one data problem (430 rows) | raising issues with the organizers; showing judges our care |

---

## Key definition: which column is "Visits"?

The brief asks for three metrics: **Visits, Pounds distributed, Individuals served**. The data has no column called "Visits".

| Metric | Column we use | Why |
|---|---|---|
| **Visits** | `HouseholdsReg` | The brief (p. 2) and glossary define a visit as *"one trip by one household"* |
| **Pounds** | `PoundsReg` | direct |
| **Individuals** | `IndividualsReg` | = adults + children + seniors (true in every row) |

⚠️ **Known conflict:** The Food Group's own published monthly "visits" (`TFG_SlideDeck.pdf`, slide 7) match **`IndividualsReg`**, not `HouseholdsReg`. Our Step 10 check confirms it: individuals / published = 0.97–1.01 every month. We follow the brief's written definition and have asked the organizers to confirm. If they say Visits = `IndividualsReg`, it's a one-line change. This matters most for Q7, where predictions are scored.

---

## Step 1: Choose columns (why the `…Reg` columns)

**What:** keep 13 of 58 columns (IDs, year/month, county, site type, food bank, six `…Reg` metrics) and rename them (`HouseholdsReg` → `visits`, etc.).

**Why:** each metric appears in five versions: `Reg` (regular distributions), `Extra`, `Produce`, `Holiday` and `Total`. The data dictionary marks everything except `Reg` as **Deprecated**. We proved this in the data, not just the dictionary:
- `HouseholdsTotal` = `HouseholdsReg` in **every row** (same for Individuals, Pounds, Adults). Children and Seniors differ in exactly 1 row, the row with a negative seniors value fixed in Step 6.
- Every `Extra`, `Produce` and `Holiday` column is **completely empty**.

So all activity is recorded under `Reg`. "Reg" means **regular**, not "registered".

**Outcome:** a 13-column table with readable names.

**Why not `…Total`?** Identical numbers, but the dictionary calls it deprecated, and "we used the documented field" is easier to defend. Other columns like `Meals`, `People` and `UniqueVisitsReg` are deprecated or almost empty (`UniqueVisitsReg` has 19 values out of 28,287).

---

## Step 2: Remove rows with an impossible month

**What:** remove **26 rows** whose month number is **0** (25 rows) or **15** (1 row).

**Why:**
- The 25 "2023, month 0" rows are all northeast Minnesota (St. Louis, Carlton, Lake and Cook counties, all supplied by Second Harvest Northland), entered in one batch on **2024-01-16**. Their `DateForSearch` field says **Dec 2022**.
- The "2023, month 15" row (site 1148, Polk) has `DateForSearch` **Mar 2024**.
- **Every one of these sites already has a real row for that month, with different numbers.** E.g. site 1218: real Dec 2022 = 993 households; "month 0" row = 1,461.

Possible explanations: a correction batch with a broken month field, catch-up entries, or a typo for the single month-15 row. The data can't tell us which.

**Outcome:** 26 rows removed (6,381 households = 0.05% of all visits). Listed in the issues log.

**Why not move them to Dec 2022 and add them?** If they're re-entries, St. Louis County's Dec 2022 would be double-counted. **Why not replace the existing rows?** No evidence the new numbers are more correct. → **Raise with organizers.**

---

## Step 3: Tag site types (`site_group`)

**What:** map the 12 `AgencyType` labels into 5 groups:

| `site_group` | AgencyType labels | Share of visits |
|---|---|---|
| `food_shelf` | Brick and Mortar Site(s), Food Shelf, Mobile, Tribal Program, College Campus Program | 91.3% |
| `outreach` | Outreach Program | 7.5% |
| `unknown` | *(blank)* | 1.0% |
| `other` | Other Non-Profit, Agency or Tribal Nation | 0.1% |
| `meal` | Meal Program(s), On-Site Meal Programs | **0.0%** |

**Why:** Q1 compares need with **food shelf** use. Meal programs serve cooked meals, a different service, and they record almost nothing in these columns (2,722 rows, 3,778 visits in total). Outreach delivers groceries (e.g. to homebound seniors), so it *is* food shelf-style activity.

**Outcome:** every row keeps its data plus a `site_group`. The county-month file **excludes only `meal`**.

**Why not delete meal rows?** Tagging is reversible; deleting isn't. Any question can choose its own filter from the site-month file.

---

## Step 4: Fix counties → 87 official counties + FIPS

**What:**
1. **Fill blank counties** from `Organization.xlsx`, looking up the site ID: 132 blank → 16 filled.
2. **Merge splits and fix spellings:**
   - `Hennepin-Minneapolis`, `Hennepin-Suburbs`, `Hennepin` → **Hennepin**
   - `Ramsey-Saint Paul`, `Ramsey-Suburbs`, `Ramsey` → **Ramsey**
   - `Saint Louis` → **St. Louis**; `Lac Qui Parle` → **Lac qui Parle**
3. **Attach the FIPS code** (5-digit county ID, e.g. 27053 = Hennepin) from the Map the Meal Gap county list.
4. **Drop** the 116 rows still without a county.

**Why:** Map the Meal Gap, Census and SNAP only know the **87 official counties**, and the reliable way to join them is FIPS. Names are written differently in every source (`St. Louis` / `Saint Louis` / `ST. LOUIS`). Without the merge, Hennepin and Ramsey, the two largest counties (8,000+ rows), wouldn't join to Map the Meal Gap at all, and Lac qui Parle would look like it had zero food shelves.

**Outcome:** every row has `county` + `fips`. `county_original` keeps the raw name, so the Minneapolis/Suburbs split is still there if Q6 wants it. The 116 dropped rows hold 84,209 visits (0.67%). **86 of 87 counties** have data. **Wilkin County has no reporting food shelf at all**, which is a finding for Q1, not an error.

**Why not keep the splits?** No public dataset splits counties that way. **Why not guess the county for the 116?** Nothing in the data indicates it.

---

## Step 5: Fix duplicate site-months

**What:** where one site has 2+ rows for the same month:

| Kind | Count | Action |
|---|---|---|
| blank row + reported row | 5 | remove the blank one |
| exact copies | 11 | keep one |
| two **different** real values | 28 site-months (56 rows) | **add together**, `flag_dup_summed = True` |

**Why:** we need exactly one row per site per month, otherwise county totals double-count. The "different values" pairs look like **two distribution points sharing one ID**. E.g. site 1103 (St. Louis) reports ~211 *and* ~58 households **every month** from Jan–Jun 2024, a steady second stream, not a one-off correction.

**Outcome:** 28,145 → 28,101 rows. Every site-month appears once.

**Why not "keep the latest"?** Both rows have the **same modification timestamp**, so there is no "latest". **Why not "keep the larger"?** It would throw away the second distribution point. → **Worth confirming with organizers.**

---

## Step 6: Impossible values, typos and outliers

**What:**

| Rule | Rows | Action |
|---|---|---|
| Negative pounds / seniors | 4 + 1 | set to missing |
| **Clear typo:** visits > 10× that site's median month **and** visits > individuals (and > 1,000) | **7** | visits set to missing, `flag_typo_fixed` |
| Any visits / individuals / pounds > 10× the site's median (above a floor), not a clear typo | 43 | `flag_outlier`, kept |
| Other rows with visits > individuals | 145 | `flag_hh_gt_indiv`, kept |

**Why:**
- A negative weight or headcount is impossible.
- Households can't exceed individuals (every household has ≥ 1 person). When that **and** a 10× jump happen together, it's clearly a typo:
  - **Waseca site 1197, Jul 2023: 273,385 households** with 646 people (normal month ≈ 434). This one row was more than all of Waseca's other months combined, and Waseca would have looked like the most over-served county in Minnesota.
  - **Ramsey site 1304, Mar 2025: households = pounds = 83,909**, i.e. pounds typed into the households box.
  - Hubbard 1417 (6,670 vs. ~78 normal), Marshall 1277, Dakota 15306, Polk 1245, Hennepin 1083.
- One warning sign alone isn't enough to change data, so we only flag.

**Outcome:** 2023 statewide visits fall from 2,757,778 to 2,482,146, almost entirely the Waseca typo. Remaining households > individuals rows are 0.82% of visits.

**Why not delete everything above 10×?** Some spikes are real: Scott County site 15309 is high for three months in a row with matching individuals and pounds (likely real growth or a new program). **Why not just flag the typos?** They'd stay in every total unless every analysis remembered to filter them.

---

## Step 7: Blank vs. zero months

**What:** keep **blank** metrics as missing (`reported = False`). Keep **zeros** as zeros.

**Why:** two kinds of "nothing" mean different things:

| | Count | Meaning |
|---|---|---|
| Blank | 1,928 site-months | the site **didn't send numbers**; people probably came |
| Zero | 1,577 site-months | the site **reported** that nobody came (or it was closed) |

If blanks were treated as zero, a site that forgot to report March would look like it served nobody, so its county would look **falsely under-served**, the exact thing Q1 is hunting for.

**Outcome:** 92–94% of site-months are reported in every year. The county file counts missing site-months so gaps are visible.

**Why not fill blanks with the site's average?** That invents data. We may impute later for Q7, and if so, we'll do it explicitly and say so.

---

## Step 8: Save the site-month file and the issues log

- **`foodshelf_site_month.csv`**: 28,101 rows × 22 columns, all site types, with flags `flag_dup_summed`, `flag_typo_fixed`, `flag_outlier`, `flag_hh_gt_indiv` and `reported`. Filter any flag out in one line: `df[~df.flag_outlier]`.
- **`foodshelf_issues_log.csv`**: 430 rows, one per problem (removed, changed, filled or flagged), with the **original numbers**, the issue and the action taken.

| Issue | Action | Rows |
|---|---|---|
| invalid month number (0 or 15) | removed | 26 |
| county blank, not in Organization either | removed | 116 |
| county blank in org_FSStats | filled from Organization | 16 |
| duplicate: blank copy | removed | 5 |
| duplicate: exact copy | removed | 11 |
| duplicate: two different values | summed | 56 |
| negative pounds / seniors | set to missing | 5 |
| visits typo | visits set to missing | 7 |
| value > 10× site median | flagged, kept | 43 |
| more households than individuals | flagged, kept | 145 |

---

## Step 9: County-month file

**What:** add up sites to **county × month**, for **all 87 counties × 55 months** (Jan 2022 – Jul 2026), **excluding meal programs**.

Columns: `fips`, `county`, `month`, the six metrics, `n_sites`, `n_sites_reported`, `n_sites_missing`.

**Why:** Q1 (summed to years), Q4/Q5 (monthly patterns) and Q7 (forecast) all work at county level.

**Details:**
- Metrics are sums over **reported** sites. If **no** site in a county reported that month, the metric is **blank**, not 0.
- Counties with no sites still appear, with `n_sites = 0`. That's **Wilkin**, so its absence is explicit rather than silently missing.

**Why not include meal programs?** A different service with ~0 recorded activity (Step 3).

---

## Step 10: Sanity checks

**Statewide totals (after cleaning, meal programs excluded):**

| Year | Visits (households) | Individuals | Pounds | Months |
|---|---|---|---|---|
| 2022 | 1,963,236 | 5,626,130 | 118.7M | 12 |
| 2023 | 2,482,146 | 7,625,430 | 140.0M | 12 |
| 2024 | 2,862,391 | 8,994,350 | 155.6M | 12 |
| 2025 | 3,016,327 | 9,055,404 | 151.1M | 12 |
| 2026 | 1,755,606 | 5,422,702 | 89.2M | 7 (Jan–Jul) |

**Against The Food Group's published visits** (slide 7): our **individuals** are within 0.1–0.8% of their published monthly visits for Jan–Mar 2025 and Jan–Mar 2026 (Apr 2026 is 2.7% lower, likely late reports). This confirms (1) our cleaning keeps the totals intact, and (2) their "visits" = individuals (see the Visits definition above).

---

## Questions to raise with the organizers

1. **Visits definition:** is "Visits" `HouseholdsReg` (brief definition) or `IndividualsReg` (matches TFG's published counts)? Critical for Q7 scoring.
2. **"Month 0" rows:** 25 rows entered 2024-01-16 for northeast MN sites with `_Month = 0`. What are they?
3. **Duplicate site-months with different values** (e.g. site 1103, Jan–Jun 2024): two distribution points under one ID, or corrections?
4. **Visit typos** (e.g. Waseca site 1197, Jul 2023: 273,385 households): confirm the correct values?

All supporting rows are in `foodshelf_issues_log.csv`.
