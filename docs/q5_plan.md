# Q5 plan: SNAP enrollment and food shelf use

**Brief:** *"SNAP gives a household money to buy food. A food shelf gives a household food directly. Do the two move together, or does one replace the other? The SNAP benefits may change from time-to-time, what happens to food shelf activity when the SNAP benefits change? Does the relationship between SNAP benefits and food shelf activity differ across locations?"*
**Note in brief:** state the SNAP source, grain and **publication lag**.

---

## Data

| | File | Grain | Period |
|---|---|---|---|
| SNAP | `Data/processed/snap_2022_2026_clean.csv` (originals: `Data/SNAP_20XX_RAW.pdf`) | county agency × month | Jan 2022 – **Mar 2026** |
| Food shelf | `Data/processed/foodshelf_county_month.csv` | county × month | Jan 2022 – Jul 2026 |
| Poverty / population | `Data/processed/poverty_2022_2024_clean.csv` | county × year (ACS 5-yr) | 2022–2024 |
| Rural | `rural` / `rucc_2023` in `mmg_mn_county_2022_2024.csv` | county | — |

**Overlap used for Q5: Jan 2022 – Mar 2026 (51 months).**

**Source note for the slide:** MN DHS Reports and Forecasts Division, *"SNAP and State-Funded Food: Minnesota Cases, Recipients, and Payments"*. County agency × month. Publication lag ≈ 3 weeks for monthly figures (final annual version the following January). Includes Minnesota's state-funded food benefit.

🚨 **Never re-download the 2026 SNAP PDF**: a newer copy may contain August 2026 → disqualification.

---

## Decisions (settled)

| # | Decision |
|---|---|
| Q36 | Source verified: CSV matches the DHS PDFs for 2022–2026. Use `snap_2022_2026_clean.csv`. |
| Q37 | **Enrollment** = `snap_people`. **Benefit size** = `snap_expenditure / snap_people` ($ per person per month). Total dollars only as context. |
| Q38 | All three food shelf metrics; lead with **visits** in slides. |
| Q39 | Part B story = **year-over-year % change** (same month vs. a year earlier, removes seasons). **Changed during build:** the backup regression was replaced by a **matched-sites check** (same food shelves both years), because growth wasn't a straight line and a trend regression would mistake that bend for a SNAP effect. |
| Q40 | County "dose-response" scatter: **one dot per county**, x = change in SNAP $ per resident around Apr 2023, y = % change in visits (YoY). Plus rural vs. urban colouring. |
| Q41 | SNAP geography = **same rule as the Q1 notebook**: 82 single-county agencies join by name → FIPS; MNPrairie (Dodge+Steele+Waseca) and WPHS (Grant+Pope) only as combined regions; the 7 tribal-overlap counties (Mahnomen, Becker, Clearwater, Beltrami, Mille Lacs, Pine, Aitkin) left out of county SNAP rates. |
| Q42 | **Short, focused notebook** that ends with a **slide-ready section** (2–3 charts + 3 key sentences). |
| Q43/44 | **Hybrid** presentation: normal slides with static charts + **one live Mosaic page** (screenshot backup in the deck). |
| Q45 | Part A answered **both ways**: over time (statewide) and across counties. |
| Q46 | Team is learning Mosaic in STAT 436 → build the Mosaic page as a **Quarto + Observable JS (`vgplot`, DuckDB-WASM)** page, like the course notes. One linked view, built last. |

---

## Parts and how each is answered

### A. Together or replace?
1. **Over time (statewide, monthly):** plot SNAP people and food shelf visits on one timeline. Correlate their **year-over-year changes** (not raw levels, which both trend up).
   - Same direction → they **go together**. Opposite → one **replaces** the other.
2. **Across counties:** SNAP participation relative to poverty (`snap_people / poverty_count`) vs. visits per 1,000 residents, by county (Spearman).

### B. What happens when SNAP benefits change?
- **Event 1, April 2023:** COVID emergency boost ends. Benefit per person **$260 → $160** (−42% dollars in one month), enrollment unchanged.
  - Chart: food shelf visits **YoY %** by month, Jan 2022 – Mar 2026, with a line at Apr 2023.
  - Table: YoY change for 6 months before vs. 6 and 12 months after, for visits, pounds, individuals.
- **Event 2, late 2025 – 2026:** enrollment falls **440k → 421k (−4%)** (SNAP cuts). Same YoY view: did food shelf visits rise faster?
- Minor: October cost-of-living increases (mention only).
- Backup: regression of monthly visits on a before/after indicator + month-of-year effects + trend.

### C. Does it differ across locations?
- Dose-response scatter (Q40): SNAP $ lost per resident (Apr 2023) vs. % change in visits, one dot per county, coloured rural/urban.
- Simple comparison: average visit increase in rural vs. urban counties; note tribal-area counties separately.

### D. Message for lawmakers
- One or two sentences, e.g. *"When SNAP benefits fell in April 2023, food shelf visits rose X% above their usual growth within N months; counties that lost more SNAP per resident saw larger increases."* (fill in from results).

---

## Outputs

- `notebooks/05_q5_snap_foodshelf.ipynb`: short notebook, Parts A–D, ending with a slide-ready section
- `docs/05_q5_snap_foodshelf.md`: in-depth explainer (What / Why / Outcome / Why-not)
- Slide charts: (1) timeline SNAP vs. visits, (2) YoY visits with the Apr 2023 line, (3) county dose-response scatter
- Mosaic (later): linked county scatter + timeline

## Limitations to state
- SNAP is by county **agency**; 12 counties handled specially (Q41).
- The emergency-allotment end affected **every** county at once, so there's no untouched comparison group; the county dose-response helps but isn't proof.
- Food shelf data counts where the food shelf is, not where visitors live.
- Visits were already rising every year (2022 → 2025 records), so effects are measured as change *beyond* the trend.
