# 01b · Q1 extension: do new public county factors explain the mismatch?

Companion to `notebooks/01b_q1_factor_extension.ipynb`. The notebook has the code and short notes. This file explains **every step in plain language**: what we did, why, what we found, and why we didn't do it another way. Read it before presenting the "why the mismatch?" part of Q1.

Builds on: `notebooks/q1_need_vs_foodshelf_activity.ipynb` (the main Q1 notebook, not changed). Factors: `notebooks/06a_build_county_factors.ipynb`, `notebooks/06b_acs_factors.ipynb` (ACS via the Census API) and `notebooks/06c_extra_factors.ipynb` (MN DEED cost of living, USDA SNAP retailers, MN WIC), sources in [source_register.md](source_register.md). Charts: `outputs/q1b/`. Test table: `Data/processed/q1b_factor_tests.csv`.

---

## The question

The last part of Q1 asks us to use **public data** on county characteristics (poverty, rural share, distance, SNAP, …) to explain **why Feeding America's need estimates and food shelf activity don't match** in some counties.

The main Q1 notebook already answered with about 10 characteristics: **geography, access and the food shelf network** line up with the mismatch, while poverty, vehicle access, rural share and SNAP don't. We then collected **27 more public factors**. This notebook asks: **do any of them explain the mismatch better, or change the story?**

## Words used in this document

| Term | Meaning |
|---|---|
| **MMG** | Feeding America's *Map the Meal Gap*: estimated food-insecure people per county |
| **Gap** (Method A, from Q1) | how far a county's food shelf activity is from what counties with similar MMG need record, in log2 units. **+1 = twice the expected activity, −1 = half, 0 = as expected.** We use the 2022–2024 average, per metric (visits, pounds, individuals) and overall |
| **Mismatch group** | Q1's labels: 10 counties persistently **lower** than expected, 16 persistently **higher**, 60 with **no persistent mismatch** |
| **Spearman ρ (rho)** | −1 to +1: do two things rise together? Uses ranks, so one extreme county can't fake a pattern |
| **p-value** | how likely a pattern this size would appear by pure chance |
| **Multiple testing** | if you run 156 tests, about 8 will have p < 0.05 **by luck alone** |
| **FDR / q-value** | Benjamini–Hochberg *false discovery rate* correction: the p-value adjusted for how many tests we ran. **q < 0.05 = "survives correction"** |
| **Standardized coefficient** | how much the gap changes when a factor goes up by one *standard deviation* (a "typical" difference between counties), with the other factors held constant |
| **Robust (HC3) standard errors** | confidence intervals that don't assume every county is equally noisy |
| **VIF** | variance inflation factor: how much a predictor overlaps with the others. Under 5 = acceptable |
| **Adjusted R²** | share of the variation explained, with a penalty for each extra predictor |
| **Leave-one-out (LOO) R²** | predict each county with a model fitted **without** it. It tests whether a model works on counties it hasn't seen. If it is much lower than the ordinary R², the model is fitting noise |

---

## Step 1: Reuse Q1's gaps, and check they reproduce

- **What:** loaded the saved Q1 tables (`q1_county_profiles.csv`, `q1_county_year_mismatch.csv`). Then rebuilt the gaps from scratch from the cleaned food shelf and MMG files.
- **Why:** the brief's question is about Q1's mismatch, so we must use exactly Q1's definition. Rebuilding proves the saved tables are what we think they are.
- **Found:** exact match. Slopes 1.20 (visits 2022) and 1.15 (pounds 2023), Nicollet's overall gap −1.76, and every county's gap equal to the saved value (differences ~10⁻¹⁵).
- **Why not recompute everything here:** two copies of the same logic can drift apart. One source of truth (the Q1 notebook) plus a check is safer.

## Step 2: Organize the factors into hypotheses

We grouped every factor under one reason the brief gives for need not turning into food shelf visits:

| Group | Factors (★ = new) | What we'd expect if this is the reason |
|---|---|---|
| **a. Hardship / economy** | ★unemployment (BLS), ★SAIPE poverty & child poverty, ★median income, ★% below 150% poverty, ★low-income housing cost burden, ★income inequality, ★uninsured, ◆housing cost burden ≥30% and ≥50% (all households); poverty (ACS) | **No link**, because MMG's own model already uses poverty, unemployment and income |
| **b. Eligibility gaps** | % food-insecure above the SNAP limit, ★% children free/reduced lunch, SNAP participation, ◆% households on SNAP, ◆**SNAP gap** (poverty households without SNAP) | + (people who can't get SNAP rely on food shelves) |
| **c. Physical access** | distance, % > 10 mi, % nearest food shelf in another county, no-vehicle, rural share, ★grocery stores per 10k, ★USDA low access (3 versions), ★broadband, ★no internet, ★long commutes | − (barriers mean less activity) |
| **d. Awareness / stigma / social** | ★limited English, ★social associations, ★census self-response, ★loneliness, ★American Indian share, ★tribal-area share, ★Hispanic share, ◆foreign-born, ◆non-white or Hispanic | mixed |
| **e. Network / supply** | sites per 10k, visits per site, SuperShelf share, food bank region | + for more/busier sites |
| **f. Demographics** | ★65+, ★under 18, ★disability, ★single parents, ◆65+ living alone, ◆disabled people in poverty | − for seniors and disability |

- **Left out:** the County Health Rankings *food environment index*, because it is built partly from MMG food insecurity (circular). Also the SVI summary percentiles, which just combine factors already listed.
- **Grocery stores:** County Business Patterns hides counts below 3, so 17 small counties are blank. We gave them 1 store (the midpoint of 0–2), then checked the result without them. Same answer.
- **Year-varying factors** (unemployment, SAIPE) are averaged over 2022–2024, the same years as the gaps.
- **◆ = ACS factors added later** from the Census API (`06b_acs_factors.ipynb`), averaged over the 2018–22, 2019–23 and 2020–24 windows. That makes **46 factors (35 new)**. ACS `pct_aian_alone` and `pct_hispanic_acs` are *not* added, because SVI's American Indian and Hispanic shares are already in the list and are practically identical (r ≥ 0.999).

## Step 3: One factor at a time (Spearman + FDR)

- **What:** Spearman ρ between each of 46 factors and each of 4 gaps (overall, visits, pounds, individuals), plus a Kruskal–Wallis test for the food bank region: **188 tests** (156 in the first version + 32 for the 8 ACS factors). FDR correction over all of them; a looser version within each metric as a second view.
- **More tests = a slightly stricter correction.** Adding the ACS factors raises every q-value a little. `q1b_factor_tests.csv` keeps both: `q_fdr` (all 188 tests) and `q_fdr_before_acs` (the first 156; blank for ACS rows). ρ and p of the original rows are unchanged.
- **Why FDR:** with 86 counties and 188 tests, about 9 "significant" results would appear by luck alone. Without correction we would "discover" things that aren't there.
- **Found** (chart: `outputs/q1b/q1b_factor_heatmap.png`):
  - **No factor survives the main FDR correction.** The best is Q1's own **% of residents whose nearest food shelf is in another county**: ρ ≈ −0.33, p ≈ 0.002, q ≈ 0.10 over 188 tests (0.08 over the first 156). With the looser within-metric FDR it still passes for visits (q ≈ 0.049), and so does the food bank region (visits, q ≈ 0.049).
  - The next strongest are all Q1 factors too: % over 10 miles (−0.27), sites per 10k (+0.25), average distance (−0.24).
  - **New factors show essentially nothing:** only **1 of 108** new-factor tests has even p < 0.05, fewer than the ~5 expected by chance. It is % below 150% poverty vs. the pounds gap, ρ ≈ −0.25, and the sign is the "wrong" way: poorer counties record slightly *less* than expected.
  - **The 8 ACS factors add nothing:** 1 of 32 tests has p < 0.05 (% non-white vs. the individuals gap, ρ ≈ +0.23, q ≈ 0.31; that's household size, Step 8). The **SNAP gap** has ρ ≈ −0.05 with the overall gap; % on SNAP −0.09; housing burden −0.08/−0.12; foreign-born +0.12; seniors alone and disability-in-poverty ≈ 0.
  - Hardship measures are all near zero (unemployment +0.07, SAIPE poverty −0.11, child poverty 0.00, income +0.14).
  - New access measures are weak: grocery stores −0.02, USDA low access −0.03 to −0.13, broadband +0.09. **Distance to a food shelf matters; distance to a grocery store doesn't.**
- **Why Spearman and not Pearson:** a few counties (Mahnomen, Cook, Nicollet) are extreme. Ranks stop one county from creating a correlation.

## Step 4: Mismatch groups (lower / no / higher)

- **What:** compared the medians of each factor across the 10 lower, 60 no-mismatch and 16 higher counties (Kruskal–Wallis, Mann–Whitney, FDR).
- **Found:** **nothing survives FDR** (smallest q ≈ 0.19; 0.23 with the ACS factors added). The only factors with p < 0.05 are Q1's: the cross-county share (medians 19% / 12% / 5%) and visits per site-month. No new factor separates the groups.
- **Why still show it:** it's the most intuitive view for a slide ("what do the under-served counties have in common?"). But groups of 10 and 16 counties give little power, so a "no" here is weak evidence on its own.

## Step 5: A small multivariable model

- **Rule, fixed in advance:** in each of the six groups, take the factor with the strongest |ρ| with the overall gap. Drop the most overlapping one until all VIF < 5. That gives **at most 6 predictors**, and we use the same six for every metric so the metrics can be compared. Excluded from selection: visits per site-month (built from activity, so circular) and SNAP (missing for 12 counties).
- **Selected:** % below 150% poverty (new), % food-insecure above the SNAP limit, % nearest food shelf in another county, census self-response (new), sites per 10k, % with a disability (new). All VIF < 4.5.
- **Found** (chart: `outputs/q1b/q1b_coefficients.png`):
  - **Only the cross-county share is clearly significant, for every metric:** about −0.27 per SD (p ≤ 0.006). One SD more residents whose nearest food shelf is across the line ≈ 0.83× the expected activity.
  - Sites per 10k is borderline positive. Disability leans negative (p ≈ 0.05 for individuals only; one of 24 coefficients, so not convincing). Poverty and census response are ≈ 0.
  - R² ≈ 0.22–0.24, the same level as Q1's model.
- **Why one per group:** with 86 counties, a model with 15+ predictors would fit noise. One per hypothesis gives each explanation a fair, equal chance.

## Step 6: Do new factors add anything beyond Q1's access factors?

- **What:** **baseline** = Q1's access + network model (cross-county share, % over 10 mi, sites per 10k, food bank region). **Full** = baseline + the three new factors selected above. We compare adjusted R², run a robust test of "all new coefficients = 0", and compute **leave-one-out R²**. We also add each of the 27 new factors **alone** to the baseline (108 tests, FDR).
- **Found:**

| | Adj. R² baseline | Adj. R² + new | Δ | LOO R² baseline | LOO R² + new |
|---|---|---|---|---|---|
| All metrics | 0.23 | 0.27 | +0.04 | 0.04 | 0.02 |
| Visits | 0.27 | 0.30 | +0.03 | 0.11 | 0.08 |
| Pounds | 0.16 | 0.22 | +0.07 | −0.02 | −0.02 |
| Individuals | 0.23 | 0.25 | +0.03 | 0.02 | −0.01 |

  - In sample, the new factors add a little (robust test p ≈ 0.003–0.06). **Out of sample (LOO), they add nothing or make it worse.** The in-sample gain is overfitting.
  - One at a time, **% American Indian** is the only new factor that passes FDR. **It is one county: Mahnomen** (35% American Indian, 2.5× expected activity, in the otherwise-low North Country region). Without Mahnomen: p ≈ 0.43. Using ranks: p ≈ 0.36. Mahnomen is an interesting case (White Earth Nation), but not a statewide pattern.
- **Why LOO:** adjusted R² still rewards a model for fitting quirks of these exact 86 counties. LOO asks whether it can predict a county it hasn't seen.

## Step 6b: The ACS factors in the nested / LOO check

- **What:** the same two checks as Step 6 for the 8 ACS factors (notebook section 8b). Steps 5–7 keep the first version's candidate list, so their numbers don't change.
  1. Each ACS factor **alone** on top of the baseline: 8 × 4 = 32 tests, FDR within the 32 and across all 140 add-one tests.
  2. The Step 5 rule applied to ACS factors only (strongest |ρ| per group, VIF < 5) → a block of 4: severe housing burden, % households on SNAP, % non-white, seniors living alone. Added to the baseline together.
- **Found:**
  - **One at a time:** none of the 32 tests reaches even p < 0.05 (smallest p ≈ 0.09). Nothing passes FDR either way.
  - **As a block:** adjusted R² +0.00 to +0.04, robust Wald p = 0.31–0.68, and **LOO R² falls for every metric** (overall 0.04 → −0.03). Noise, not explanation.
- **Meaning:** the SNAP gap, housing burden, immigration, isolation and disability-in-poverty, as measured by the ACS at county level, do not explain why counties record more or less than MMG expects.

## Step 6c: Three more datasets (cost of living, SNAP retailers, WIC)

- **What** (notebook section 8c): nine factors built in `06c_extra_factors.ipynb`, tested exactly like the others.
  - **MN DEED cost of living** (one edition, no year in the file): affordability gap (family-of-3 budget ÷ median income), family-of-3 yearly budget, family-of-3 monthly food cost, single-adult required hourly wage.
  - **USDA FNS SNAP retailer locator**: SNAP retailers per 10k and full-service SNAP stores per 10k (2022–24 average), miles to the nearest full-service SNAP store (2024, population-weighted, same method as Q1's food shelf distance), net change in SNAP retailers per 10k 2022→2025.
  - **MN Department of Health WIC**: WIC infants + children per 100 children under 5 (2022, the latest year available).
- **Test count:** 9 × 4 = **36 new tests**, so the Spearman family grows from **188 to 224**. In `q1b_factor_tests.csv` the original 188 rows are **unchanged** (`q_fdr` is still their 188-test value); a new column `q_fdr_incl_06c` has the 224-test value for every row, and the 36 new rows (batch `06c extra`) use the 224-test value in `q_fdr`.
- **Found:**
  - **One at a time:** none of the 36 tests reaches even p < 0.05 (about 2 would by chance). On the overall gap: affordability gap −0.08, DEED food cost +0.11, SNAP retailers per 10k −0.03, full-service SNAP stores per 10k +0.10, **miles to the nearest full-service SNAP store −0.11** (p = 0.32), net change in SNAP retailers +0.07, WIC uptake −0.08. Smallest q = 0.75.
  - **The old leader with 224 tests:** % nearest food shelf in another county, q = 0.12 (0.10 over 188). Still nothing passes the all-tests FDR. With 56 tests per metric, the looser within-metric FDR no longer passes either (cross-county share and food bank region for visits: q = 0.058, was 0.049).
  - **Added to the access/network baseline one at a time:** 4 of 36 have p < 0.05 (DEED single-adult wage for visits, +0.27 per SD, p = 0.02; affordability gap for pounds, −0.15, p = 0.03; family budget for visits), none survives FDR (q ≥ 0.34 within the 36, ≥ 0.44 over all 176 add-one tests).
  - **As a block** (DEED food cost, WIC uptake, grocery distance; VIF < 5): adjusted R² **falls** by 0.01–0.02, robust Wald p = 0.70–0.96, LOO R² falls for every metric (overall 0.04 → −0.09).
- **Meaning:** cost of living, grocery access and WIC uptake do not explain the Q1 mismatch. Grocery distance and food shelf distance are correlated across counties (ρ = 0.71), yet only food shelf distance lines up with the gap (−0.24 vs −0.11). Same lesson as Step 3: **the food shelf network, not the food retail environment**.

## Step 7: Cross-validated sanity checks

- **What:** (1) LOO where the **selection rule is re-run inside every fold**, so the held-out county never influences which predictors get picked. (2) A random forest on all factors, with out-of-bag R² and permutation importance.
- **Found:**
  - Out-of-sample R² is **very low for every model** (0.02–0.11; random forest 0.03).
  - The random forest's top factor is again **% nearest food shelf in another county**, well ahead of the rest.
- **Meaning:** the cross-county share is a consistent *average tendency*, but no combination of public county data can **predict** which specific counties will be off. Most of the mismatch is local: particular sites, a big regional food shelf, recording habits.

## Step 8: Do the metrics need different explanations?

- **What:** (1) compared the 46-factor ρ profiles between metrics; (2) tested what explains the *difference* between gaps: `pounds − visits` (≈ food per visit, relative to expected) and `individuals − visits` (≈ people per visit).
- **Found:**
  - **The shared part is the same for all three metrics:** ρ profiles correlate 0.85–0.96, and the gaps themselves 0.81–0.94.
  - **Pounds-specific part = food bank network** (q ≈ 0.01). Channel One counties give less food per visit than expected (median −0.40 log2 ≈ 0.76×). North Country and Second Harvest Heartland ≈ as expected.
  - **Individuals-specific part = household size:** more people per visit where there are more foreign-born residents (ρ ≈ +0.39, ACS), more non-white or Hispanic residents (+0.38, ACS), more children (+0.37) and more Hispanic residents (+0.35); all q ≤ 0.02 over 94 tests. Larger households mean more individuals per trip.
- **So "pounds = supply, visits = access"?** Partly. Access explains what all three share. The food bank network explains the extra pounds part. Household composition explains the extra individuals part.

## Step 9: Change over time (2022 → 2024)

- **What:** within each county, did the gap change when unemployment, poverty or income changed?
- **Found:** **rising poverty goes with a *falling* gap** (visits and individuals ρ ≈ −0.30, q ≈ 0.03 within these 9 tests). Unemployment and income changes: nothing after correction.
- **Meaning:** MMG's need estimate moves with poverty, but food shelf activity doesn't follow, so the gap shrinks. It's more evidence that **hardship sits inside the MMG estimate, not in the mismatch**.

## Step 10: Robustness

- Grocery stores without the 17 suppressed counties: still ρ ≈ −0.02.
- Dropping Q1's possible data-quality counties (Douglas, Grant, Stevens): nothing changes. The cross-county share gets slightly stronger (−0.37).

## Step 11: Children: child food insecurity vs. children served

- **What:** Q1 in miniature for children (notebook section 16). Need = MMG food-insecure children (`fi_children`) and child FI rate. Activity = food shelf `children` (children in served households, summed over months, so person-visits like `individuals`). Child population = ACS B09001 (`pop_under18_acs`). 2022–2024, 86 counties. Then the Method A gap for children (log2 children served vs. log2 food-insecure children, per year, averaged), compared with the all-ages individuals gap. Chart: `outputs/q1b/q1b_children.png`.
- **Found:**
  - **Counts line up, rates don't** (same as Q1 for all ages): ρ = 0.90 for counts; children served per child vs. child FI rate ρ = 0.11 (p = 0.29).
  - **Children are not under-served relative to adults.** Statewide they are 36% of individuals served vs. 32–35% of food-insecure people. Children served per food-insecure child: 11 (2022) → 16 (2024) person-visits a year.
  - **The child gap repeats the all-ages gap** (ρ = 0.96), with the same cross-county link (ρ = −0.35). The same counties are under half of expected (Pope, Benton, Lac qui Parle, Nicollet, Scott, Grant, Brown, Carlton, Todd, Lincoln) and the same hubs over double (Steele, Washington, Rice, Renville, Blue Earth).
  - **One child-specific outlier: Lincoln** (children −1.72 vs. all ages −0.49), a small county (≈ 180 food-insecure children); worth asking the local food shelf how it records household members.
- **Seniors:** MMG has **no county senior food-insecurity estimate** (Feeding America's *State of Senior Hunger* is state-level), so no senior version. Seniors are 11–13% of individuals served, falling from 13.1% (2022) to 10.9% (2024).
- **Why it matters:** it rules out "children are the hidden gap" at county level. The mismatch is about where food shelves are, for children as for everyone.

---

## What it means

**Which new factors matter?** None, once we account for running many tests (188 including 8 ACS factors from the Census API; **224** with the 9 factors from `06c`: DEED cost of living, SNAP retailers, WIC). The only "hit" (American Indian share) is Mahnomen County alone.

**Which don't?** Hardship (unemployment, poverty, income, housing cost from SVI and ACS), eligibility (free/reduced lunch, SNAP receipt, the ACS **SNAP gap**), immigration (foreign-born), seniors living alone, disability in poverty, grocery and supermarket access (including exact SNAP retailer counts, closures and distance to the nearest full-service SNAP store), cost of living (MN DEED), WIC uptake, internet, commuting, language, social ties, loneliness, tribal area, age, disability, single parents.

**Why hardship can't work:** Feeding America's estimate is *built from* poverty, unemployment and income. The gap is "activity minus what MMG's hardship-based estimate predicts". A factor already inside the estimate can't explain the leftover. That isn't a failed analysis. It tells us the mismatch comes from **how need turns into recorded visits**, not from how much need there is.

**Does it change the Q1 story?** **No. It strengthens it.** 44 more factors couldn't beat Q1's access finding: **counties record less than expected where residents' nearest food shelf is across the county line or far away, and more where sites are dense or busy.** The food bank network matters too, especially for pounds.

**Be honest on stage:** the strongest factor narrowly misses the strictest correction (q ≈ 0.10 over 188 tests, 0.08 over the first 156, 0.12 over all 224; within-metric for visits it passes at 188 tests, q = 0.049, but not at 224, q = 0.058), and no model predicts held-out counties well (LOO R² ≤ 0.11). County characteristics describe a tendency, not a forecast for each county.

## What's still missing (top 3, from [data_wishlist.md](data_wishlist.md))

1. **Food bank partner-agency hours and capacity** (needs a request): the network is the second-strongest signal and drives the pounds-per-visit difference.
2. **Tribal reservation boundaries + FDPIR participation:** our tribal proxy misses Red Lake, and Mahnomen hints that tribal food programs interact with food shelf use.
3. ~~SNAP gap, ACS B22003~~ **obtained** (Census API, `06b`) and tested: it does not explain the mismatch (ρ ≈ −0.05). **SNAP retailer locations and WIC** have also been obtained (`06c`) and tested (Step 6c): neither explains the mismatch.

Beyond public data: **client ZIP codes** would measure cross-county use directly. That remains the single most useful addition.

## Slide (3 sentences)

1. We tested 44 new public county factors (including the Census API's SNAP gap, housing burden, foreign-born and seniors living alone, MN DEED cost of living, USDA SNAP retailer access and MN WIC participation) against the Q1 mismatch, and **none survives correction for multiple testing**. Hardship can't explain deviations from Feeding America's estimate because the estimate is built from hardship.
2. **The strongest explanation is still cross-county access:** counties where more residents' nearest food shelf is in another county record less than expected (ρ ≈ −0.33). It ranks first in every method, and new factors add no out-of-sample power.
3. The three metrics share this story. **Pounds** differences also track the **food bank network**, and **individuals** differences track **household size**. Children follow the same pattern as everyone (ρ = 0.96).

Charts: `outputs/q1b/q1b_slide.png` (main), `outputs/q1b/q1b_factor_heatmap.png` (appendix), `outputs/q1b/q1b_coefficients.png`, `outputs/q1b/q1b_children.png` (children).

## Data rule

Only food shelf data for 2022–2024 and public factors with vintages up to 2025 (SVI 2022, CHR 2025 release built on ≤ 2024 data, USDA access 2019, SNAP retailer records to December 2025, WIC 2022, DEED's current edition) are used. Nothing dated August 2026 or later. The September-2026 SNAP dashboard file was not opened.
