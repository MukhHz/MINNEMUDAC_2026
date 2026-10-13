# 00 · Findings for the slides (Q1, Q4, Q5, Q6, Q7)

One page per question, in the order we'd present. Every number below comes from an executed notebook or saved CSV (source given in brackets); the detailed explainers are the `docs/NN_*.md` files. Last checked against the notebooks on 2026-10-12, after re-running `06c`, `01b` and `06` with the three new datasets (MN DEED cost of living, USDA SNAP retailers, MN WIC).

---

## The one story

**Need is driven by hardship, prices and SNAP. Recorded demand is driven by access and the food shelf network. Where the two diverge, the cause is mostly access.**

1. **Need** (how many people lack food) follows hardship: poverty, income, unemployment, and Map the Meal Gap (MMG), which is built from them. When **prices** rise (Q4) and when **SNAP benefits** fall (Q5), more people need help, statewide and about equally everywhere.
2. **Demand** (food shelf visits, pounds, individuals) follows that statewide pressure **over time**, with a delay (about 15 months after a grocery-price surge; 6–10 months after the April 2023 SNAP cut). But **across counties** it barely follows need per resident (Q1: ρ ≈ 0 by 2024; Q6: ρ = 0.11).
3. **What decides where demand is recorded** is **access and the network**: how far people live from a food shelf, whether their nearest one is across the county line, and where big regional sites are (Q1, Q6). 44 more public county factors (hardship, eligibility, cost of living, grocery access, WIC...) don't beat this (Q1b).
4. **The divergence** (Q6) between need and recorded activity is therefore mostly an **access gap**: remote rural counties with high need record little, while regional hubs record more than their own need. WIC uptake, an independent food program, is high exactly where Q6 says need exceeds activity.
5. **The forecast** (Q7) works because statewide demand is stable month to month; the county errors come from local shocks (a site opening or closing), not from need.

---

## Q1 · Need vs. food shelf activity

**The question:** Do Feeding America's need estimates and the three food shelf metrics tell the same story, where do they disagree, and what county characteristics explain it?

**Answer in one sentence (slide title):** *Need and food shelf activity agree on county size but not on intensity; where they disagree, distance and cross-county access explain it, not hardship.*

**Key numbers**
- Totals agree, mostly because of county size: Spearman ρ = 0.89–0.92 between food-insecure people and visits / pounds / individuals in every year (population alone gives the same 0.88–0.92). [Q1 notebook, sections 6.2 and 15]
- Intensity doesn't: food insecurity *rate* vs. activity *per resident*, Spearman −0.01 (visits), 0.02 (pounds), 0.00 (individuals) in 2024. [Q1 section 15]
- 2022 → 2024: estimated need +25%, visits +46%, pounds +31%, individuals +60%. [Q1 section 6.1]
- 12 counties are persistently ≥ 2× above or ≤ ½ of what similar-need counties record: lower = Nicollet, Pope, Lac qui Parle, Norman, Roseau; higher = Steele, Washington, Rice, Renville, Mahnomen, Pipestone, Olmsted. [Q1 section 25]
- Strongest explanation: % of residents whose nearest food shelf is in another county, ρ = −0.33 with the mismatch gap (regression ≈ −0.26 per SD; Nicollet: 59%, next to Mankato). The characteristics explain 22% of the variation, 34% with the food bank region. 44 more public factors add **nothing that survives correction** (224 tests; best q = 0.12) and no out-of-sample power (leave-one-out R² ≤ 0.11). [Q1 sections 32 and 36; Q1b sections 5, 8c, 9; `q1b_factor_tests.csv`]

**Interpretation**
- County need estimates are a **weak guide** to where food shelf activity concentrates; county size and site locations matter more.
- A county can look underserved when its residents are served **next door** (Nicollet → Blue Earth); hub counties look over-served for the same reason.
- Hardship can't explain the gap, because MMG is built from hardship. The gap is about **how need turns into recorded visits**.

**Recommended action:** Plan with per-resident, travel-distance and site-level views, not county totals; investigate the five persistently low counties (Nicollet, Pope, Lac qui Parle, Norman, Roseau) with their food banks.

**Limitations:** associations across 86 counties (Wilkin has no food shelf); straight-line distance; cross-county use is inferred, not observed; MMG is a model estimate; the strongest factor is borderline after multiple-testing correction (q = 0.10 over 188 tests, 0.12 over 224).

**Further data needed:** **client ZIP codes** (measures cross-county use directly); driving distance and mobile-pantry routes; food bank partner-agency hours and capacity.

**Charts to use:** `outputs/q1b/q1b_slide.png` (strongest factors + new factors add nothing out of sample); `outputs/q1b/q1b_factor_heatmap.png` (appendix).

---

## Q4 · Grocery prices and food shelf activity

**The question:** Do more people come to food shelves when grocery prices rise, at once or after a delay, in all three metrics, and are there other cycles?

**Answer in one sentence (slide title):** *Food shelves feel a grocery-price surge about 15 months later, not right away, in all three metrics.*

**Key numbers**
- Midwest grocery inflation peaked at **15.2% in Aug 2022**; same-food-shelf visit growth peaked at **+49% in Feb 2024**, 18 months later. Grocery prices are **28.5%** higher in Jul 2026 than in Jan 2021 and never fell. [Q4 notebook, steps 0 and 9]
- Same-month correlation ≈ 0 (visits −0.06, individuals +0.19, pounds +0.10); best delay **15 months** for all three (correlation 0.78 / 0.89 / 0.83). [Q4 step 3]
- Against 2,000 fake inflation series that also pick their best delay: individuals p = 0.008, pounds p = 0.016, visits p = 0.064. Bootstrap 80% range of the delay: 12–17 months (visits). [Q4 step 3]
- With the SNAP-cut window as a control, the price effect at lag 12 holds for individuals (2.73 → 2.73) and pounds (1.46 → 1.64) but halves for visits (1.93 → 0.77). [Q4 step 4]
- Seasons: August busiest (visits index 105), December lowest (92); pounds per visit fell from 61 lb (2022) to 50 lb (2025). [Q4 steps 5–6]

**Interpretation**
- A price surge is an **early warning with about a year's lead**: demand starts rising ~6 months later and peaks 12–17 months later.
- **Pounds measure supply as well as demand**: when more people came, each visit got less food.
- The data can't separate grocery prices from the general cost-of-living squeeze (all-items inflation lines up just as well, p = 0.024).

**Recommended action:** Track Midwest food-at-home and all-items CPI monthly (free, released mid-month); fundraise and secure food in the year **after** a surge; watch pounds per visit as a rationing signal. All-items inflation rose to 5.0% in May 2026 on gasoline, so prepare for above-normal growth from roughly mid-2027 if it persists.

**Limitations:** essentially **one** inflation episode (2021–23); 43 months of overlapping YoY data; the price surge overlapped with the SNAP cut and the end of other pandemic help, so effect sizes are upper bounds; prices are regional (Midwest).

**Further data needed:** a second price episode (time); food bank inventory/TEFAP supply data to separate supply from demand in pounds.

**Charts to use:** `outputs/q4/q4_1_inflation_vs_growth.png` (main); `outputs/q4/q4_2_lag_profile.png` (the delay).

---

## Q5 · SNAP and food shelf use

**The question:** Do SNAP and food shelf use move together or replace each other, what happens when SNAP benefits change, and does it differ by place?

**Answer in one sentence (slide title):** *When SNAP benefits per person fell almost 40% in April 2023, food shelf visits grew much faster for a year, everywhere, while SNAP enrollment barely moved.*

**Key numbers**
- Benefit per person fell from **$260 to $160** a month (Mar → Apr 2023). [Q5 notebook, summary table]
- Mar 2022 → Mar 2026: SNAP enrollment **−3%**, food shelf visits **+92%**, individuals **+99%**; month-by-month link between their YoY changes ≈ 0 (ρ = −0.06, p = 0.73 for visits). [Q5 A1]
- Visits YoY growth before / in the year after / two years after the cut: **+21% / +31% / +8%**; same food shelves only: **+11% / +31% / +10%**. Peak 6–10 months after the cut (+49% in Feb 2024). [Q5 B2–B3]
- Counties that lost more SNAP per resident did **not** see bigger jumps: ρ = +0.01 (p = 0.97, 66 counties). Across counties, SNAP per 1,000 vs visits per 1,000: ρ = +0.12 (p = 0.31). [Q5 C3, A2]

**Interpretation**
- SNAP and food shelves are **neither substitutes nor simple partners** at county level: food shelf growth came from beyond SNAP enrollment.
- Benefit **levels** matter: the cut lines up with a year of faster visit growth, even at the same food shelves.
- The jump was statewide and similar everywhere, so the cut is **one important contributor alongside prices** (Q4), not the only cause.

**Recommended action:** Treat any SNAP benefit cut as an early warning (expect more visitors over the next 6–12 months), prepare everywhere rather than only high-SNAP counties, and use the April 2023 episode in policy arguments that **benefit levels**, not only eligibility, drive food shelf demand.

**Limitations:** no untouched comparison group; the "before" period is 3 months; SNAP is reported by county office (12 counties handled specially: shared and tribal offices); SNAP data ends March 2026.

**Further data needed:** monthly SNAP by county of residence (not office) and SNAP applications/closures; later SNAP months (beyond the cutoff, for future work only).

**Charts to use:** `outputs/q5/q5_b1_visits_yoy.png` (main); `outputs/q5/q5_a1_snap_vs_visits_index.png` (SNAP flat, visits climbing).

---

## Q6 · Divergence between need and activity

**The question:** Build a measure that shows where need is likely larger than food shelf activity shows, compare it with the three metrics, and explain the disagreement.

**Answer in one sentence (slide title):** *Fourteen mostly rural counties, led by Swift, Nobles, Wadena, Chippewa and Norman, have need far above their food shelf activity, and distance explains much of it.*

**Key numbers**
- Need index = equal-weight average of 8 public hardship indicators (no activity, no access measures). Need vs. activity per resident: Spearman **ρ = 0.11**. [Q6 notebook, sections 5 and 8]
- Divergence = need percentile − activity percentile. **14 of the top 15** "need above activity" counties stay in the top 15 in ≥ 75% of 16 method versions (still 14 of 15 with the two DEED cost-of-living versions added, 18 versions); top 5: Swift +83, Nobles +76, Wadena +63, Chippewa +63, Norman +62. [Q6 sections 10, 12, 12c]
- In meals: statewide, food shelves give out **107%** of the meal gap (2024), but the county median is **63%** and 24 of 86 counties are below 50% (Norman 19%; Steele 266%). Coverage agrees with divergence (ρ = −0.80 for pounds). [Q6 section 10b]
- Explanation: % of residents > 10 miles from a food shelf, ρ = +0.52 with divergence (+12.3 points per SD in the HC3 regression); distance to the nearest **full-service SNAP grocery store** adds to that model (+15.9 points per SD, q = 0.004; adjusted R² 0.38 → 0.45), but it overlaps with food shelf distance (ρ = 0.71): it is **remoteness**. Store counts, closures and cost of living add nothing. [Q6 sections 13, 13c, 13f]
- Validation: WIC uptake per young child (2022) correlates **0.72** with the need index and **0.03** with food shelf activity, and is higher in the top-15 counties (median 47 vs 40 per 100 children under 5). [Q6 section 12c]

**Interpretation**
- The divergence counties are mostly **rural and remote** (median 99% rural; 19.6% of residents > 10 miles from a food shelf vs 5.7% elsewhere); 8 of the 15 are in the North Country or Second Harvest Northland regions and none in Channel One's. The "activity above need" counties are metro and regional hubs (Washington −94, Olmsted −81, Anoka −78).
- Part of the gap is **cross-county use** (activity counted where the shelf is): Nicollet drops out once activity is reallocated to residents' counties; 13 of 15 stay.
- Independent signals (WIC uptake) say the **need is real** where activity is low.

**Recommended action:** Prioritise outreach, mobile pantries and capacity checks in the robust underserved counties (Swift, Nobles, Wadena, Chippewa, Norman, Todd, Aitkin, Clearwater, Grant, Carlton, Benton, Becker, Pine, Morrison); start where residents are far from both food shelves and full-service groceries; partner with WIC clinics as referral points.

**Limitations:** county averages hide pockets of need; small counties (< 10k people) have wide margins; divergence is relative (ranks); activity is counted where the shelf is; DEED cost of living has no year and WIC stops at 2022; associations, not causes.

**Further data needed:** client ZIP codes; tribal program (FDPIR) participation and reservation boundaries; WIC 2023–2024; 211 food-help requests by county.

**Charts to use:** `outputs/q6/q6_divergence_map.png` (where); `outputs/q6/q6_need_vs_activity_quadrant.png` (need vs activity). Backup: `outputs/q6/q6_meal_gap_coverage.png`.

---

## Q7 · August 2026 forecast

**The question:** Forecast August 2026 visits, pounds and individuals for each of Minnesota's 87 counties, using only information up to July 31, 2026.

**Answer in one sentence (slide title):** *We forecast about 238,000 visits, 13.0 million pounds and 739,000 individuals for August 2026, with county errors about 40% below last-year's-August.*

**Key numbers**
- Submitted method: **county-by-county selection**: each county uses whichever of five robust forecasts (seasonal naive, damped 3-month YoY, local-model selection, their blend, recent 3-month mean) had the lowest error on that county over the previous 12 months. Visits used the recent mean in 33 counties, damped YoY in 21, the blend in 14, seasonal naive in 10, local selection in 8. [`forecast_august_2026/submission/README.md`]
- Statewide totals: **237,861 visits** (80% range 221,209–258,297), **12,994,439 lb** (12.19M–13.62M), **738,532 individuals** (697k–802k). [`submission/statewide_forecast.csv`; sums of `Undergraduate_Predictions_Submit.csv`]
- Backtest (31 monthly origins, Jan 2024 – Jul 2026): county WAPE **9.5% / 8.9% / 9.1%** (visits / pounds / individuals) vs **15.3% / 14.5% / 15.4%** for seasonal naive (38–41% lower) and 10.7% / 10.8% / 10.6% for the blend; statewide error 4.8% / 3.7% / 4.7%; bias ≈ 0. [`submission/county_backtest_summary.csv`]
- 101 model variants (statistical, panel ML, deep learning, structural) were tested in one leakage-safe harness; none beat seasonal naive significantly, and "pick the best of 101" did worse out of sample than simple methods. [`report/forecasting_report.tex`, abstract]

**Interpretation**
- Statewide food shelf demand is **stable**; the forecast's main job is to catch **local level shifts** (e.g. Mille Lacs gained a site in April 2026: 1,550 visits forecast instead of the blend's 991).
- Simple, county-tailored methods beat complex models, which over-fit one period.

**Recommended action:** Use the county forecasts for August allocation and staffing; re-run monthly with the same script; flag counties whose chosen method switches to "recent mean" as places where something changed (new or closed site).

**Limitations:** one-month-ahead accuracy only; the final method was chosen among four county-tailoring variants after seeing results (after correcting, pounds and individuals stay significant, visits borderline); Wilkin predicted 0 (no site in the data); external predictors (SNAP, hotline calls) were tested and rejected.

**Further data needed:** site openings/closures and hours known in advance; planned mobile-pantry schedules.

**Charts to use:** `forecast_august_2026/report/figures/county_backtest.pdf` and `forecast_august_2026/report/figures/statewide_series.pdf` (Q7 figures live in the report folder, not `outputs/`).

---

## Recommendations for The Food Group (the brief's four decisions)

1. **Allocation.** Allocate on **need per resident and distance**, not county totals or past activity alone: past activity under-counts remote counties and over-counts hubs (Q1, Q6). Use the Q7 county forecasts for the month-ahead amounts, and add a lead-time buffer when grocery or overall inflation surges (≈ 15 months, Q4) or SNAP benefits drop (6–12 months, Q5).
2. **Where to add food shelves / mobile pantries.** The robust Q6 counties, starting with those where many residents live > 10 miles from a food shelf **and** far from a full-service grocery store: Swift, Chippewa, Norman, Clearwater, Becker, Marshall (> 25% of residents beyond 10 miles from a food shelf), and Red Lake (no full-service SNAP store). Check Wadena (short distances but low activity) for hours, stock and reporting before adding sites.
3. **Policy argument.** SNAP benefit **levels** matter: after the April 2023 cut (≈ −40% per person), visits grew 31% in a year at the same food shelves, while enrollment barely moved (Q5). Price surges hit a year later (Q4). Food shelves can't absorb both: protect benefit levels and fund food shelves ahead of the delay.
4. **Measuring results.** Track per county: activity per resident, **meal-gap coverage** (pounds ÷ 1.2 ÷ MMG meal gap; Q6), pounds per visit (rationing signal; Q4), and Q6 divergence each year. Start collecting **client ZIP codes** (even a sample) so cross-county use can be measured instead of inferred: it is the biggest open uncertainty in Q1 and Q6.

---

## Appendix A · Data sources

Full details (exact series, vintage, publication lag, link): [source_register.md](source_register.md).

| Source | Geo grain | Time grain | Why chosen |
|---|---|---|---|
| The Food Group food shelf data (`org_FSStats`, `Organization`, hotline) | site → county | monthly, Jan 2022 – Jul 2026 | competition data; the three demand metrics |
| Feeding America Map the Meal Gap (MMG2025, MMG2026) | county | annual 2022–2024 | the only county food-insecurity estimate for every MN county; named in the brief |
| MN DHS SNAP monthly reports | county agency | monthly, Jan 2022 – Mar 2026 | the only monthly sub-state SNAP source |
| BLS CPI-U food at home, Midwest (`CUUR0200SAF11`) + checks | Midwest region | monthly, to Jul 2026 | groceries specifically, monthly, includes MN |
| Census ACS 5-year (S1701, B08201, B22003, B25070/B25091, B05002, B03002, B09020, C18130, B09001) | county | 5-year windows ending 2022–2024 | detail with margins of error; 1-year ACS missing for most MN counties |
| Census SAIPE, PEP, County Business Patterns; BLS LAUS | county | annual 2022–2024 | single-year official estimates and denominators |
| CDC SVI 2022; County Health Rankings 2025; USDA food access (FARA 2019, SRAM 2025) | county (from tracts) | one vintage | ready-made vulnerability and access measures |
| Census 2020 urban/rural, block-group population centers, TIGERweb, county shapes | block group / county | 2020 / 2023 | % rural and population-weighted distances |
| **MN DEED Cost of Living** (new) | county | one edition, no year in file | the only MN county basic-needs budget (housing, child care, food, transport, taxes) |
| **USDA FNS Historical SNAP Retailer Locator** (new) | store point → county | stores active 1 July 2022–2025 (file ends Dec 2025) | exact store counts by type, closures, and points for grocery distance |
| **MN Dept. of Health WIC participation by county** (new) | county | calendar year 2020–2022 | an independent food-program uptake measure to validate the need index |

## Appendix B · August-data compliance

- **No data dated August 2026 or later is used anywhere.** Food shelf data ends July 2026 (asserted in Q6 and Q7 code); BLS CPI August 2026 values existed online and were **dropped in memory before saving** (Q4 asserts `date.max() <= 2026-07-01`); SNAP ends March 2026; the Q7 pipeline checks every source's maximum month ≤ 2026-07 and that every forecast is built only from months before its target (`forecast_august_2026/submission/cutoff_check.txt`: all PASS).
- The new datasets: SNAP retailer records end **31 December 2025** (asserted in `06c`); WIC covers 2020–2022; the DEED file has no dates.
- `snap-dashboard-data-through-september-2026.xlsx` (and its copy in `Data/external/`) was downloaded after the July 31 cutoff and contains months up to September 2026. It is **not read by any Q1, Q4, Q5 or Q6 notebook, nor by the submitted Q7 model**. It was only tested in `forecast_august_2026/experiments/`, using months at least 2 months before each forecast target (never August 2026), and rejected as a predictor (see `Data/external/README.md`). **Recommendation:** delete this file from the repo before submission so no August-or-later data is even present.
