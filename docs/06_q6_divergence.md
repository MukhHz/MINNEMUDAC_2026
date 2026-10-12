# 06 · Q6: Where is need larger than food shelf activity shows? Explained

Companion to `notebooks/06_q6_divergence.ipynb`. The notebook has the code and short notes. This file explains **every step in plain language**: what we did, why, what we found, and why we didn't do it another way. Read it before presenting Q6.

Output table: `Data/processed/q6_county_need_divergence.csv`. Charts: `outputs/q6/`.

---

## The question

Food shelf data shows **where people arrive**. It does not show where people need help and don't get it. The brief asks us to:

1. Build a **new measure of need** that uses more than demand, with public data.
2. **Compare** it with the three food shelf metrics (visits, pounds, individuals).
3. Find counties where the two **diverge**.
4. As in Q1, look at **county characteristics** that might explain the disagreement.

## Words used in this document

Need / demand terms follow the challenge glossary (`Glossary_of_Terms.docx`) exactly.

| Term | Meaning |
|---|---|
| **Need** | people who lack enough food, *including people not interacting with the system* (awareness, distance, transport, stigma, eligibility...). Measured here with public hardship data. |
| **Demand** | people actively seeking or receiving food help. Here: food shelf **visits**, **pounds**, **individuals** per 1,000 residents. |
| **Unmet need** | people needing food help who don't get it, or not in full. |
| **Latent demand** | need that never becomes a request (awareness, stigma, eligibility uncertainty). |
| **Unmet demand** | a request the system can't fill (stockout, location, hours). |
| **Visits** | one household making one trip (`HouseholdsReg`) |
| **Individuals** | people served (adults + children + seniors) |
| **Pounds** | pounds of food given out (part supply, part demand) |
| **z-score** | how far a county is from the state county average, in standard deviations. 0 = average, +1 = clearly above. |
| **Percentile** | a county's rank on a 0-100 scale. 90 = higher than 90% of counties. |
| **Robust z** | like a z-score but using the median and the typical distance from it (MAD), so one extreme county can't stretch the scale. |
| **PCA (principal component analysis)** | see "PCA explained simply" below. |
| **Spearman correlation (ρ)** | −1 to +1: do two things rank counties the same way? Uses ranks, so one extreme county can't fake a pattern. |
| **p-value** | how likely a pattern this size is by pure chance. ≤ 0.05 = probably real. |
| **VIF** | checks whether regression predictors measure the same thing. Above ~5 is a warning. All of ours are ≤ 4.2. |

---

## Data

| | File | Gives | Years |
|---|---|---|---|
| Food insecurity | `mmg_mn_county_2022_2024.csv` (Feeding America Map the Meal Gap, **must be cited**) | `fi_rate`, `pct_fi_above_snap_threshold` | 2022-2024 |
| Hardship (yearly) | `county_factors_2022_2024.csv` (BLS LAUS, Census SAIPE, Census PEP) | unemployment, median income, population | 2022-2024 |
| Hardship (ACS) | `poverty_2022_2024_clean.csv` (ACS S1701 5-year) | deep poverty (<50% FPL) | 2022-2024 windows |
| Vulnerability | `county_factors_static.csv` (CDC SVI 2022, County Health Rankings 2025, USDA food access) | housing cost burden, disability, children in single-parent homes, uninsured; also the access characteristics | one vintage |
| Food shelf activity | `foodshelf_county_month.csv`, `foodshelf_site_month.csv` | visits, pounds, individuals | 2022-2024 |
| Access / network | `q1_county_profiles.csv` (Q1) | distance, % > 10 mi, % nearest shelf in another county, sites per 10k, main food bank, SNAP rate | 2022-2024 |
| Hotline | `Data/Incoming Call.xlsx` | calls by caller county | 2022-2024 (only rows dated 2022-2024 used) |
| Locations (for reallocation) | Census 2020 block-group population centers; site blocks from `Organization.xlsx` + Census TIGERweb (cached in `Data/local/`) | where people live / where shelves are | 2020 |
| Map | Census cartographic boundaries 2023 (`cb_2023_us_county_500k`) | county shapes | 2023 |
| Cost of living (sensitivity) | `county_extra_factors_static.csv` (MN DEED Cost of Living, built in `06c_extra_factors.ipynb`) | family-of-3 basic-needs budget ÷ median income (affordability gap) | one edition, no year in file |
| WIC (validation) | `county_extra_factors.csv` (MN Dept. of Health WIC participation by county, PDFs) | WIC infants + children per 100 children under 5 | 2022 (file covers 2020–2022) |
| SNAP retailers (explanation) | `county_extra_factors.csv` / `_static.csv` (USDA FNS Historical SNAP Retailer Locator) | SNAP stores per 10k, distance to nearest full-service SNAP store, closures | stores active 1 July 2022–2025 (file ends Dec 2025) |

**Q6 uses 2022-2024**, the years where Map the Meal Gap and food shelf data overlap. Nothing dated August 2026 or later is used.

---

## Step 1: What goes into the need index, and what stays out

### 1a. Need ≠ demand
- **What:** the need index uses **only public, non-food-shelf data**. No visits, pounds or individuals.
- **Why:** we later compute "need minus demand". If demand were inside need, we'd be comparing demand with itself.

### 1b. Access barriers stay out
- **What:** distance to a food shelf, sites per resident, supermarket access, no-vehicle households, rurality, tribal land, broadband, limited English are **not** in the need index. They are used in Step 6 to **explain** divergence.
- **Why:** they describe whether need can **turn into** demand, not how much need exists. If "far from a food shelf" were part of need, a remote county would score high *because* it's remote, and then finding that remoteness explains divergence would be circular.
- **Why not include them "because they make need worse":** true in life, but then the measure couldn't answer the brief's second half (*why* do need and activity disagree?).

### 1c. Choosing the indicators (redundancy screen)
- **What:** 21 candidate indicators grouped into 8 **dimensions** of hardship: food insecurity, poverty, income, jobs, housing, disability, family structure, health insurance. In each dimension we keep the first indicator (in a preference order fixed beforehand) whose Spearman correlation with every indicator already kept is **≤ 0.80**.
- **Kept (8):**

| Dimension | Indicator | Source |
|---|---|---|
| Food insecurity | `fi_rate` | Map the Meal Gap |
| Poverty | deep poverty rate (< 50% of the poverty line) | ACS |
| Income | median household income (reversed: lower = more need) | SAIPE |
| Jobs | unemployment rate | BLS |
| Housing | low-income housing cost burden | CDC SVI |
| Disability | % with a disability | CDC SVI |
| Family | % children in single-parent homes | County Health Rankings |
| Insurance | % under 65 uninsured | County Health Rankings (SAHIE) |

- **Dropped as duplicates:** the SAIPE and ACS poverty rates, below-185%/150% poverty, child poverty, child FI: each correlates 0.82-0.87 with `fi_rate` (Map the Meal Gap is itself modelled from poverty, unemployment, income, disability...).
- **Dropped on meaning:**
  - *FI above the SNAP limit*: says **which channel** food-insecure people can use, not **how many** need help, and is almost a mirror image of the below-185% poverty rate (ρ ≈ −0.9). It's used as an explanatory variable instead (as in Q1).
  - *Free/reduced lunch eligibility*: the glossary warns FRPL is breaking down as schools adopt universal meals (CEP).
  - *No high-school diploma*: a cause of low income, not hardship itself.
- **Why ≤ 0.80:** a common rule of thumb for "nearly the same thing". Keeping three poverty rates would give income poverty triple weight just because it was measured three ways.

---

## Step 2: Three versions of the need index

All 8 indicators are turned into **z-scores within each year** (so a 3% unemployment rate and a $70,000 income share one scale). The headline is the 2022-2024 average.

1. **Equal weight:** the average of the 8 z-scores. "Every kind of hardship counts the same."
2. **PCA (PC1):** weights chosen by the data (below).
3. **MMG only:** just the food insecurity rate. Shows what we add beyond Map the Meal Gap.

### PCA explained simply
Imagine 87 counties as points in an 8-dimensional space (one axis per indicator). PCA finds the **one direction** along which counties spread out the most, a single "summary axis". Each indicator gets a **loading** (weight) saying how much it points along that axis.
- **Found:** PC1 explains **53%** of the variation (eigenvalue 4.3; next is 1.2). Every loading is positive: food insecurity 0.47, disability 0.41, income 0.40, deep poverty 0.35, uninsured 0.34, unemployment 0.30, single-parent 0.26, housing burden 0.24. So PC1 is a **general hardship** factor, and we oriented it so higher = more need. PC2 (15%) contrasts housing burden / single parents / deep poverty (more urban hardship) with unemployment / disability (more rural, older counties).
- Chart: `outputs/q6/q6_need_index_pca.png`.

### Which one is the headline?
- **Rule (set beforehand):** if equal weight and PCA rank counties nearly the same (ρ ≥ 0.95 and ≥ 8 of the same top 10), use **equal weight**, because it's easier to explain; use PCA only if they disagree and PC1 clearly dominates.
- **Found:** ρ(equal weight, PCA) = **0.99**, top-10 overlap **10/10**; ρ(equal weight, MMG only) = 0.93, top-10 overlap 7/10.
- **Decision:** **equal-weight index** is the headline.
- **Why not PCA:** it gives the same answer with harder-to-explain weights. **Why not MMG only:** close, but our index moves 3 of the top-10 counties and adds hardship dimensions MMG doesn't directly show (housing, insurance, family).

### Count version (for allocation)
- **What:** an index says *where* need is relatively high; allocation needs *how many*. We put the index on Map the Meal Gap's scale (regress `fi_rate` on the index, R² = 0.91) to get a **need-adjusted rate**, then × population = **persons in need** (596,000 statewide vs 579,000 from MMG rates). Columns `need_rate_adj`, `need_persons`.
- `*_gap_count` = annual activity a county *would* record at the **median county's** activity per person in need, minus what it records. **Why the median, not the state total:** Hennepin and Ramsey hubs would otherwise set the bar and make nearly every other county look short.

---

## Step 3: Demand, the three food shelf metrics

- **What:** annual visits, pounds and individuals per 1,000 residents (Census population), 2022-2024, meal programs excluded. Each kept **separately**, plus a **combined** demand score (average of the three robust z-scores of log activity).
- **Missing reports (same as Q1):** a county-year with no reports is missing, not zero; county-years with < 12 months or > 10% of site-months unreported are flagged `incomplete` (Beltrami 2022-24, Big Stone 2022, Douglas 2023, Grant 2022, Stevens 2024) and left out of the 3-year average when the county has a complete year.
- **Why logs and robust z:** activity per resident is very skewed (a few hub counties); otherwise one county would dominate.
- **Found:** the three metrics agree with each other (ρ 0.83-0.94).

---

## Step 4: How much do need and demand agree?

- **Found:** per resident, **barely at all**: Spearman ρ = **0.11** (combined), 0.09-0.11 per metric. MMG-only and PCA versions give the same (0.06-0.12).
- **Meaning:** confirms Q1 with a much broader need measure. Knowing a county's hardship tells you almost nothing about how much food shelf use it records. That's exactly why a divergence measure is informative.

---

## Step 5: The divergence measure

### 5a. Headline: rank gap
> **divergence = need percentile − activity percentile** (among the 86 counties with a food shelf)

- **+60** = the county ranks 60 places-in-100 higher on need than on activity → **potentially underserved**: need is likely larger than activity shows (latent demand, unmet demand, or need met somewhere else).
- **−60** = activity far above need → regional hubs, people crossing county lines, or users who are not food insecure (Urban Institute: over a third of charitable food users are food secure).
- Computed for **visits, pounds, individuals separately** and for combined demand.
- **Why ranks:** one extreme county can't dominate; the result reads in plain words.

### 5b. Checks
| Check | Agreement with the rank gap |
|---|---|
| Robust-z gap (keeps distances, not just order) | ρ = **0.96**, 9 of top 15 shared |
| Regression residual (log activity on need; − residual) | ρ = **0.74**, 8 of top 15 shared |

- **Why the residual agrees less:** need explains almost none of demand (R² = 0.016), so the fitted line is nearly flat and the residual becomes "low activity, whatever the need". The rank gap gives need an explicit, equal say, which is what the question asks for. Both alternative versions are in the output file.
- **Two halves:** divergence correlates +0.65 with need and −0.65 with activity. A high score needs **both** high need **and** low activity; low activity alone isn't enough.
- **The three metrics agree:** visits vs individuals divergence ρ = 0.94, pounds vs the others 0.85-0.90.

---

## Step 6: Which counties diverge?

### Need above activity (potentially underserved), 2022-2024
| # | County | Need pctile | Activity pctile | Visits | Pounds | Indiv. | Combined | Robust | Note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Swift | 94 | 12 | +77 | +86 | +77 | +83 | 100% | 47% of residents > 10 mi from a food shelf; < 10k people |
| 2 | Nobles | 92 | 16 | +79 | +80 | +53 | +76 | 94% | 30% Hispanic, 11% limited English (awareness/eligibility uncertainty?); individuals less low than visits/pounds |
| 3 | Wadena | 90 | 27 | +63 | +67 | +58 | +63 | 100% | short distances, many sites: not an access story; worth a site-level look |
| 4 | Chippewa | 85 | 22 | +55 | +71 | +52 | +63 | 100% | 37% > 10 mi; 35% nearest shelf in another county |
| 5 | Norman | 66 | 5 | +63 | +65 | +62 | +62 | 100% | lowest activity in the state; 30% > 10 mi; < 10k |
| 6 | Todd | 73 | 14 | +62 | +52 | +58 | +59 | 100% | 22% nearest shelf in another county |
| 7 | Aitkin | 98 | 42 | +48 | +69 | +58 | +56 | 100% | tribal SNAP agency overlap (Mille Lacs Band) |
| 8 | Clearwater | 99 | 47 | +47 | +45 | +52 | +52 | 94% | 31% > 10 mi; tribal overlap (Red Lake / White Earth); < 10k |
| 9 | Grant | 71 | 20 | +51 | +36 | +57 | +51 | 100% | **Q1 data-quality flag** (incomplete 2022); < 10k |
| 10 | Carlton | 81 | 35 | +43 | +55 | +51 | +47 | 100% | Fond du Lac reservation area |

Also robust: Benton, Becker, Pine, Morrison (#11-15); Marshall (#14) is method-dependent (69%). Q1 flagged only Nobles, Chippewa, Norman and Benton as "lower than expected". Q6 adds counties because it uses a broader, per-resident need measure, not food-insecure *counts*.

### Activity above need (top 15, all robust except Le Sueur)
Washington (−94), Olmsted (−81), Anoka (−78), Rice, Steele, Dodge (−69), Kittson, Sherburne (−64), Wabasha (−63), Hennepin (−58), Houston, Jackson, Dakota, Pipestone, Le Sueur. Mostly **low-need metro/regional-center counties with busy sites** (Q1's "few busy regional sites" pattern). Houston is high on visits and individuals but less on pounds.

Charts: `q6_need_vs_activity_quadrant.png`, `q6_top10_by_metric.png`, `q6_divergence_map.png`.

---

## Step 6b: Meal-gap coverage, the divergence score in plain numbers

The divergence score is a **rank**: good for comparing counties, hard to say out loud. This companion turns it into a sentence a food bank can use: *"food shelves in county X give out about N% of the meals its food-insecure residents are short."* Notebook section 10b; chart `outputs/q6/q6_meal_gap_coverage.png`.

- **What:**
  - **Meal gap** (Feeding America, Map the Meal Gap) = `annual_food_budget_shortfall ÷ cost_per_meal` = meals food-insecure residents are short in a year. (MMG already counts people as food insecure for about 7 months of the year, and the weekly shortfall is about 6 meals per food-insecure person.)
  - **Food shelf meals** = pounds ÷ **1.2**. Feeding America's standard conversion is **1.2 pounds of food ≈ 1 meal** (used in its annual reports and by member food banks).
  - **Coverage** = food shelf meals ÷ meal gap. 100% = enough food to fill the whole gap.
- **Years:** headline **2024**, **2023** as a check. MMG changed its cost-per-meal method in 2023, so 2022 isn't comparable with 2024; we only compare counties **within** a year.
- **Found:**
  - **Statewide ≈ 107%** (2023: 106%): food shelves give out about as many meals as the whole meal gap. That does **not** mean the gap is closed: the food is spread unevenly and part of it goes to people who are not food insecure.
  - **The typical county covers well under its gap:** county median **63%** (2023: 67%). **24 of 86 counties are below 50%**, 16 above 100%.
  - **Lowest (2024):** Norman **19%**, Stevens 21%, Scott 21%, Swift 22%, Nicollet 23%, Lincoln 24%, Lac qui Parle 27%, Chippewa 29%. **Highest:** Steele **266%**, Rice 256%, Washington 202%, Olmsted 199%, Blue Earth 174%: regional hubs that also serve neighbours.
  - **Two lows are partly artefacts:** Scott's largest site (about 1.9 million lb in 2023) has no rows in 2024, so Scott falls from 98% to 21%; Stevens has 3 unreported months in 2024. The chart marks counties whose coverage changed more than 2× from 2023 (†) and incomplete reporting (‡).
  - **Stable:** Spearman 0.89 between 2023 and 2024.
  - **Agrees with divergence:** Spearman **−0.80 with pounds divergence**, −0.77 with combined, −0.73 with individuals. 8 of the 15 lowest-coverage counties are in the top-15 "need above activity" list.
  - **How they differ:** coverage is driven by activity (ρ = +0.86 with the pounds percentile) and hardly by need (ρ = −0.23), because the meal gap already grows with the number of food-insecure people. So coverage also flags low-activity counties with *average* need (Scott, Nicollet, Lincoln, Lac qui Parle, Roseau, Pope, Stevens), while divergence adds high-need counties (Becker, Carlton, Clearwater, Morrison, Pine, Todd, Grant). Use divergence to rank, coverage to explain.
  - **Visits/individuals analogue:** individuals served per food-insecure resident (person-visits, so a monthly visitor counts 12 times) runs from about 2 a year (Norman, Scott, Lac qui Parle) to 44–50 (Steele, Washington); it agrees with meal coverage (ρ = 0.87). Saved as `indiv_per_fi_person_2024`.
- **Caveats (say them with the number):**
  1. 1.2 lb per meal is an approximation (produce is heavy, dry goods light).
  2. Food shelves also serve people who are **not** food insecure: the Urban Institute finds **over a third** of charitable food users are food secure. So coverage is an **upper bound** on how much of the food-insecure gap is filled.
  3. Pounds are counted where the **shelf** is, not where clients live (Step 7): hubs look over-covered, their neighbours under-covered.
  4. **Wilkin** has no food shelf in the data, so no coverage value.
  5. Food shelves are only one channel (SNAP, school meals, meal programs and tribal programs also fill the gap).
- **Slide sentence:** *"In 2024, food shelves in Norman County gave out enough food for about 1 in 5 of the meals its food-insecure residents are short; in Steele County, more than 2½ times the gap, because Steele's shelves also serve neighbouring counties."*
- **Side note on `snap_threshold`:** the MMG file's `snap_threshold` is **2.00 (200% of the poverty line) for every Minnesota county**, because SNAP income limits are set by the state, not the county: MMG applies Minnesota's one SNAP gross-income threshold (200% of poverty, under broad-based categorical eligibility) to every county and every year. It is a constant, so it can't explain anything between counties; `pct_fi_above_snap_threshold` (which varies) is what we use.

---

## Step 7: Cross-county use (sensitivity)

- **Problem:** activity is counted **where the food shelf is**, not where clients live. Nicollet residents use Mankato (Blue Earth) shelves (Q1).
- **What:** rebuilt Q1's distance inputs and gave each fixed food shelf's activity to the block groups for which it is the **nearest** shelf (split by population), then summed by the residents' county. Outreach/mobile sites and sites with mismatched locations stay put. Totals are preserved exactly.
- **Found:** resident-based divergence correlates **0.91** with the headline; **13 of the top 15** stay. Biggest moves: **Nicollet +28 → −64** (cross-county use explains its gap entirely), Red Lake −15 → +36, Dodge −69 → −29, Clearwater +52 → +29, Becker +41 → +16. **Wilkin** (no food shelf) gets activity from neighbours' shelves and scores **+40**.
- **Why not the headline:** people don't always use their nearest shelf (big sites draw from further away). This is an approximation; client ZIP codes would settle it.

---

## Step 8: Stability

16 versions: headline + each year (2022, 2023, 2024) + PCA + MMG-only + 8 leave-one-indicator-out + drop data-quality counties (Douglas, Grant, Stevens) + resident reallocation.

- **Found:** every alternative correlates 0.91-1.00 with the headline; median top-15 overlap **14/15** (lowest 12/15, for year 2022 and without unemployment).
- **14 of the top 15** potentially underserved counties stay in the top 15 in **≥ 75%** of versions (11 in ≥ 94%). Same for the activity-above-need list (14 of 15).
- **Small counties:** 4 of the top 10 have < 10,000 people (Swift, Norman, Clearwater, Grant), where ACS estimates have wide margins. Flagged in `flag_small_county_lt10k`.

---

## Step 8b: Does the housing indicator matter? (ACS sensitivity)

- **What:** the need index's housing component is SVI's **low-income** cost burden (households under $75k paying ≥ 30%; one vintage, 2018–22). The new Census API data (`06b_acs_factors.ipynb`, tables B25070/B25091) gives the burden for **all** households in **each** window (2018–22, 2019–23, 2020–24). We swapped it in (≥ 30%, and severe ≥ 50%) and rebuilt the index. Notebook section 12b.
- **Found:** almost no change. The ACS burden correlates 0.87 with the SVI one. Need ranking: Spearman **0.99** with the headline, 14 of the top 15 the same. Divergence: Spearman **0.99**, **15 of 15** top counties the same (severe-burden version: 0.99, 13 of 15). Biggest moves are about 12 percentile points, in small counties (Traverse, Lake of the Woods).
- **Why we keep SVI as the headline:** it targets lower-income households, the ones most likely to need food help. The ACS version is the robustness check (and could be used yearly).

---

## Step 8c: Cost of living in the need index, and WIC as a check (`06c` data)

Notebook section 12c.

**Cost of living (MN DEED).**
- **What:** DEED's basic-needs budget for a family of 3 (2 adults, 1 child, 1.5 workers) divided by the county's median household income (SAIPE 2024) = the **affordability gap** (median county 0.84; range 0.64 to 1.06; highest Aitkin, Pine, Ramsey, Beltrami). It is hardship, so it may go in the need index. We tried (a) **adding** it as a 9th component and (b) **swapping** it for the income component.
- **Found: almost no change.** The gap overlaps income (ρ = 0.69), food insecurity and disability (0.64). (a) need ranking Spearman **0.99** with the headline (14 of the top 15 the same); divergence **0.99**, **15 of 15** top counties unchanged; largest move 10 percentile points (Cottonwood −10, Lincoln +9). (b) need 0.99 (14 of 15), divergence 0.99 (15 of 15), largest move 16 points. Counting both as extra stability versions (18 in all), **14 of 15** headline counties stay robust, as before.
- **Why it stays out of the headline:** DEED's file is a single edition with no year, so it can't be matched to 2022–2024; and it adds nothing the 8 components don't already carry.

**WIC (validation, not a component).**
- **Why not a component:** WIC is a program people sign up for, so it is partly **demand** (Rule 1). But it is demand in a **different system**, so it is a good outside check: if our need index is right, WIC should follow it; if "need above activity" counties are real, WIC should be high there even though food shelf activity is low.
- **Found:** WIC infants + children per 100 children under 5 (2022) correlates **0.72** with the need index (0.71 with the 2022-only version; 0.72 with MMG food insecurity) and **0.03** with food shelf activity. Holding need fixed, WIC and food shelf activity are unrelated (partial rank ρ = −0.07, p = 0.51). The 15 "need above activity" counties have **higher** WIC uptake: median **47 vs 40** per 100 young children (p < 0.01).
- **Meaning:** another food program reaches many young families exactly where we say need is high and food shelf activity is low. That supports the need side of the measure. Caveats: 2022 only, only mothers and young children, and partly a sign-up (demand) measure.

---

## Step 9: What explains divergence? (akin to Q1)

### 9a. Correlations (86 counties)
Each characteristic vs **need**, **activity**, and **divergence**, so we can see *which side* it works through. Chart: `q6_divergence_explainers.png`.

| Characteristic | ρ with need | ρ with activity | ρ with divergence |
|---|---|---|---|
| % residents > 10 mi from a food shelf | +0.37 | **−0.33** | **+0.52** |
| Avg miles to nearest food shelf | +0.35 | **−0.33** | **+0.49** |
| % nearest shelf in another county | −0.09 | **−0.38** | +0.20 (p = 0.06) |
| Rural share | +0.29 | −0.15 | +0.32 |
| Social associations per 10k | +0.06 | −0.27 | +0.25 |
| No-vehicle households | +0.49 | +0.20 | +0.23 |
| SNAP participation (74 counties) | **+0.68** | +0.15 | +0.41 |
| Broadband | **−0.44** | +0.17 | −0.44 |
| FI above SNAP limit | **−0.72** | +0.06 | −0.57 |
| Sites per 10k, supermarket access, tribal area | weak (|ρ| ≤ 0.16 with divergence) | | |

- **Reading it:** distance and cross-county measures work through the **activity side** (farther from a shelf → less recorded activity). SNAP, broadband and FI-above-SNAP correlate with divergence mostly **because they track need** (they're hardship mirrors), not because they lower activity.
- **Group medians (top-15 underserved vs rest):** 19.6% vs 5.7% of residents > 10 mi (p = 0.01); 5.7 vs 3.9 average miles (p = 0.01); 16% vs 7.8% nearest shelf in another county (p = 0.03); rural share 99% vs 66% (p = 0.07). No North Country / Second Harvest Northland county is in the activity-above-need group; no Channel One county is in the underserved group.

### 9b. Regression (HC3 robust SEs, 7 standardized predictors, VIF ≤ 4.2)
Combined divergence, points per 1 SD: **% > 10 mi +12.3** (95% CI 4.5 to 20.2, p < 0.01), **% nearest shelf in another county +8.7** (1.3 to 16.1, p = 0.02), no-vehicle +8.3 (p = 0.05), **broadband −16.3** (p < 0.01); sites per 10k, rural share, tribal area ≈ 0. R² = 0.43 (visits 0.39, pounds 0.36, individuals 0.44). **Adding the main food bank** raises R² to 0.57: North Country (+29, p = 0.01) and Second Harvest Northland (+35, p < 0.01) regions diverge more than Channel One, at the same distance.

### 9c. Holding need fixed
Because divergence mixes need and activity, we also modelled **activity percentile** with need as a control. At the same need: % nearest shelf in another county **−8.7** (p = 0.01), % > 10 mi −7.0 (p = 0.06), broadband **+10.7** (p = 0.01). So distance, cross-county use, and (possibly) information access are real barriers between need and recorded demand, not artifacts of the need side.

### 9d. New ACS characteristics (Census API): barriers, not hardship
Four new ACS measures describe whether need can **turn into** a visit, so they stay **out** of the need index (Rule 2) and are tested as **explanations** (notebook section 13e). 3-window averages.

| Characteristic (ACS table) | ρ with need | ρ with activity | ρ with divergence | Added to 9b model | Added to 9c model |
|---|---|---|---|---|---|
| **SNAP gap**: % of poverty households not on SNAP (B22003) | **−0.46** | −0.21 | −0.18 (p = 0.09) | p = 0.79 | p = 0.36 |
| % foreign-born (B05002) | −0.29 | +0.20 | **−0.39** (p < 0.001, FDR q = 0.001) | p = 0.64 | p = 0.48 |
| % of people 65+ living alone (B09020) | +0.17 | +0.02 | +0.10 (p = 0.38) | p = 0.18 | p = 0.69 |
| % American Indian / Alaska Native (B03002) | **+0.49** | +0.12 | +0.24 (p = 0.03, q = 0.06) | p = 0.27 | p = 0.72 |

- **None adds to the explanation.** Each one alone, and all four together, change adjusted R² by less than 0.01 (robust Wald p = 0.23 for divergence, 0.72 for activity-given-need). No added-variable test passes FDR (all q = 0.79).
- **Foreign-born** is the only strong raw link, and it runs through **both** sides: most high foreign-born counties are metro or regional centres (Ramsey, Hennepin, Watonwan, Mower, Olmsted, Scott, Dakota) with lower need and short distances. Once distance is in the model it vanishes. The exception is **Nobles** (Worthington, 21% foreign-born, highest in the state), a top underserved county: worth a closer look, but one county is not a pattern. So we find **no county-level sign** that immigrant fear lowers food shelf use (it may exist; county data can't see it).
- **AIAN share and the SNAP gap** work through the **need** side: AIAN counties are poorer, and poorer counties have *more* of their poor households on SNAP (a smaller SNAP gap). Neither means fewer visits at the same need.
- **Seniors living alone:** nothing.
- **Reliability:** AIAN shares under about 1% have CV > 30% (wide margins), but the counties that matter (Mahnomen, Beltrami, Cass, Clearwater...) are precise; the SNAP gap is precise everywhere except Lake of the Woods (± 19 points).

### 9e. SNAP retailer access (USDA FNS retailer locator, `06c` data)
Five access characteristics from every SNAP-authorized store's location and dates (notebook section 13f): SNAP retailers per 10k and full-service SNAP stores per 10k (2022–24), miles to the nearest **full-service** SNAP store (supermarket, super store, large grocery; population-weighted from Census block groups, 2024, stores across the state line included), % of residents > 10 miles from one, and the net change in SNAP retailers per 10k 2022→2025. Tested against divergence **and** meal-gap coverage (Step 6b).

| Characteristic | ρ with need | ρ with activity | ρ with divergence | ρ with coverage 2024 | Added to 9b model (divergence) | Added to 9c model (activity at same need) |
|---|---|---|---|---|---|---|
| SNAP retailers per 10k | **+0.61** | −0.03 | +0.46 | −0.26 | p = 0.73 | p = 0.73 |
| Full-service SNAP stores per 10k | +0.27 | +0.01 | +0.19 (p = 0.09) | −0.06 | p = 0.45 | p = 0.91 |
| **Miles to nearest full-service SNAP store** | +0.45 | −0.22 | **+0.50** | −0.28 | **+15.9 per SD, p < 0.001, q = 0.004** | −9.0 per SD, p = 0.01, q = 0.09 |
| % > 10 mi from a full-service SNAP store | +0.44 | −0.21 | +0.47 | −0.25 | +9.9, p = 0.04, q = 0.20 | p = 0.09 |
| Net change in SNAP retailers per 10k, 2022→25 | −0.23 | −0.09 | −0.11 (p = 0.32) | −0.03 | p = 0.89 | p = 0.53 |

- **Grocery distance adds to the divergence model:** adjusted R² **0.38 → 0.45** (q = 0.004 over 15 added-variable tests). At the same need, counties farther from a full-service store record less food shelf activity (p = 0.01, q = 0.09).
- **But it is general remoteness, not groceries as such.** Grocery and food shelf distance overlap (ρ = 0.71 for average miles; 0.63 for % > 10 mi). Each one alone fits the divergence model about equally (adj R² 0.39 vs 0.38); with both in, grocery distance keeps p = 0.04 and food shelf distance falls to p = 0.12. Read it as: **people who live far from everything record less food shelf use than their need suggests.**
- **Store counts and closures explain nothing.** SNAP retailers per 10k correlate with divergence only through need (poorer rural counties have many small stores per resident). Minnesota's SNAP network grew slightly 2022→2025 (net +102 stores), and county-level closures are few.
- **Coverage:** none of the five adds to the meal-gap coverage model (all p ≥ 0.26; all five together p = 0.93).
- **Contrast with Q1:** the same grocery distance does **not** explain the Q1 mismatch gap (Q1b Step 6c, ρ = −0.11). Q1's gap is measured against MMG food-insecure counts; Q6's divergence uses a broader per-resident need index, where remote counties rank high on need.

**Bottom line (same as Q1):** divergence is explained more by **geography, access and the food bank network** than by poverty, rurality per se, vehicles or SNAP. The SNAP retailer data sharpens "access" into **remoteness**: distance to a full-service grocery store explains divergence as well as distance to a food shelf, while store counts, closures and cost of living do not.

---

## Step 10: Outside checks and what would prove this wrong

### Checks we ran
- **SNAP:** higher in underserved counties (median 8.4% vs 6.8%). Consistent with need being real; it could also mean part of the need is met by SNAP instead. But SNAP doesn't lower food shelf activity across counties (ρ = +0.15), so it doesn't explain the gap.
- **Hotline calls (2022-2024):** **no support**: calls per 10k are the same in underserved counties and elsewhere (8.9 vs 8.7; ρ with divergence −0.11). The hotline is Twin Cities-based, and 42% of calls have no usable county, so it mostly measures awareness. Equally consistent with latent demand ("no one asks anywhere") as with "no extra need". We report it honestly as not confirming.

### What would prove the measure wrong
1. **Client ZIP data** showing residents of top-divergence counties are served in neighbouring counties at rates that close the gap (our reallocation already does this for Nicollet).
2. **Other programs** (tribal FDPIR, SNAP, school meals) clearly covering the need in Aitkin, Clearwater, Becker, Carlton, Pine (tribal areas whose food programs aren't in this data).
3. **Revisions:** the top list changes a lot when MMG or ACS estimates are revised, or is driven by small counties' noisy ACS rates.
4. **No other hardship signal:** 211 / SNAP applications from these counties no higher than elsewhere *after* accounting for awareness.
5. **Under-reporting:** food shelves in these counties missing reports (Grant is already flagged).

---

## Output file: `Data/processed/q6_county_need_divergence.csv`
One row per county (87), sorted by `rank_underserved`. Key columns:
- `need_ew` (headline), `need_pca`, `need_mmg`, `need_pctile`, `need_rate_adj`, `need_persons`
- `visits_per_1k`, `pounds_per_1k`, `individuals_per_1k`, `dz_*` (robust z of log activity), `dem_pctile_*`
- `div_visits`, `div_pounds`, `div_individuals`, `div_combined` (headline), `div_z_combined`, `div_resid_combined`, `div_combined_resident`
- `rank_underserved`, `share_top15_under`, `share_top15_over` (persistence across 16 versions)
- `*_gap_count`, flags (`flag_cross_county_gt25`, `flag_small_county_lt10k`, `flag_data_quality_q1`, `any_incomplete`), `category`, `metric_note`
- Wilkin: need only; `category = no food shelf in data`.
- **Added (Step 6b, columns appended at the end):** `meal_gap_meals_2024`, `foodshelf_meals_2024`, `meal_gap_coverage_2024` (food shelf meals ÷ meal gap, 1.0 = 100%), `meal_gap_coverage_2023` (check), `indiv_per_fi_person_2024` (person-visits per food-insecure resident), `coverage_incomplete_2024` (TRUE = incomplete reporting that year). Wilkin: blank.
- **Added (Steps 8c and 9e, `06c` data, columns appended at the end; all earlier columns unchanged, asserted):** `div_combined_with_col_gap` and `need_pctile_with_col_gap` (need index with the DEED affordability gap as a 9th component), `col_affordability_gap_fam3`, `wic_infants_children_per_100_under5_2022`, `snap_retailers_per_10k_2224`, `snap_full_mean_dist_mi_2024`, `snap_full_pct_over_10mi_2024`, `snap_net_change_per_10k_2022_2025`.

---

## Limitations
- **County level:** a county average can hide pockets of need (a reservation, a town).
- **Need indicators are estimates**, several are 5-year ACS averages or model-based (MMG, SAIPE, SAHIE); small counties have wide margins.
- **Static indicators** (SVI 2018-22, CHR 2025) don't change between years, so year-to-year changes in need come only from MMG, deep poverty, income and unemployment.
- **Activity is counted where the shelf is.** The reallocation is a nearest-shelf approximation.
- **Divergence is relative** (ranks): "underserved" means *compared with other Minnesota counties*, not an absolute shortfall.
- **Not all food help is in the data:** meal programs, tribal FDPIR, school meals, non-reporting pantries.
- **Meal-gap coverage** relies on 1.2 lb ≈ 1 meal and counts food given to food-secure people too; read it as an upper bound.
- **Extra data limits:** DEED cost of living has no year (one edition); WIC stops at 2022; SNAP retailer distance is straight-line and ignores store size, prices and hours.
- **Associations, not causes.**

## Likely judge questions
- **"Isn't your need index just Map the Meal Gap?"** They agree (ρ = 0.93) but the index moves 3 of the top 10, adds housing, insurance, family and disability, and the result holds with MMG alone (13/15 top counties shared).
- **"Why not put distance in the need index?"** Then explaining divergence with distance would be circular. We keep need (how much hardship) separate from access (whether it turns into demand).
- **"Why equal weights, not PCA?"** Same ranking (ρ = 0.99, same top 10), easier to explain. PCA confirms all 8 indicators point the same way.
- **"Couldn't a county just have few visits?"** Then it would need high need too: a high score requires both (ρ +0.65 need, −0.65 activity).
- **"Small counties are noisy."** Yes: 4 of the top 10 are < 10k people and flagged; the list barely changes across years and components.
- **"What about people crossing county lines?"** Tested: 13/15 of the top list survive reallocation; Nicollet drops out, which matches Q1.
- **"Can you say it in meals?"** Yes (Step 6b): statewide, food shelves give out about as many meals as the meal gap (about 107%), but the median county covers 63%, from 19% (Norman) to 266% (Steele). Coverage and divergence agree (ρ ≈ −0.80).
- **"Did you check SNAP take-up and immigrant share?"** Yes (9d, Census API): neither explains divergence once distance is accounted for.
- **"Is anything independent of food shelves consistent with your need index?"** Yes: WIC uptake per young child follows the need index (ρ = 0.72), not food shelf activity (0.03), and is higher in the top-15 underserved counties (47 vs 40 per 100).
- **"Is it grocery deserts?"** Partly the same thing: distance to a full-service SNAP store explains divergence about as well as distance to a food shelf (they overlap, ρ = 0.71). Store counts and closures don't matter.
- **"Why did hotline calls not confirm it?"** The hotline is metro-based and mostly measures awareness; equal call rates are also what latent demand looks like.

## Recommendations for The Food Group
1. **Prioritise outreach and capacity checks in the robust underserved counties**: Swift, Nobles, Wadena, Chippewa, Norman, Todd, Aitkin, Clearwater, Carlton, Benton, Becker, Pine, Morrison (Grant after checking its reporting).
2. **Distance first:** where > 25% of residents live > 10 miles from a shelf (Swift, Chippewa, Norman, Clearwater, Becker, Marshall), try mobile pantries / delivery and hours that fit commuters. Places that are also far from a full-service grocery store (Red Lake has none) are the best candidates: residents there are far from every food source.
3. **Awareness and language** in Nobles (30% Hispanic, 11% limited English): partner with schools, employers, community groups.
4. **Wadena** has short distances and many sites but low activity: check site hours, stock and reporting.
5. **Collect client ZIP codes** (even a sample) to measure cross-county use directly; it is the single biggest uncertainty.
6. **Coordinate with tribal programs** (Aitkin, Clearwater, Becker, Carlton, Pine) before assuming need is unmet.
7. **Work with North Country and Second Harvest Northland** regions, where divergence is higher at the same distance.
8. **Partner with WIC clinics** in underserved counties (WIC reaches a median 47 of every 100 young children there): a referral point to food shelves for families that WIC reaches and food shelves don't.
