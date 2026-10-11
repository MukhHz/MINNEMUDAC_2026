# 05 · Q5: SNAP and food shelf use, explained

Companion to `notebooks/05_q5_snap_foodshelf.ipynb`. The notebook has the code and short notes. This file explains **every step in plain language**: what we did, why, what we found, and why we didn't do it another way. Read it before presenting Q5.

Plan and decisions: `docs/q5_plan.md`. Charts: `outputs/q5/`.

---

## The question

**SNAP** (the old "food stamps") puts money on a card each month that families spend at grocery stores. **Food shelves** give families food directly. The brief asks:

1. Do SNAP and food shelf use **move together**, or does one **replace** the other?
2. What happens to food shelf use **when SNAP benefits change**?
3. Is it **different in different places**?

## Words used in this document

| Term | Meaning |
|---|---|
| **Visits** | one household making one trip to a food shelf (`HouseholdsReg`) |
| **Individuals** | number of people served |
| **Pounds** | pounds of food given out |
| **Enrollment** | how many people are on SNAP |
| **Benefit per person** | SNAP dollars ÷ people on SNAP, i.e. how much each person gets per month |
| **FIPS** | official 5-digit county ID (e.g. 27053 = Hennepin), used to join files |
| **YoY (year-over-year) change** | a month compared with the *same month a year earlier*, e.g. May 2023 vs May 2022. Removes seasons. |
| **Matched sites** | only food shelves that reported in *both* years being compared, so food shelves opening or closing can't change the result |
| **Median** | the middle value when you line numbers up; not dragged around by one extreme value |
| **Spearman correlation (rho)** | one number from −1 to +1 for whether two things rise together. +1 = always together, 0 = no pattern, −1 = always opposite. It uses ranks, so one extreme county can't fake a pattern. |
| **p-value** | roughly, how likely a pattern this size would appear **by pure chance**. Small (≤ 0.05) = probably real; large (e.g. 0.9) = nothing beyond chance. |
| **Percentage points** | the difference between two percentages: growth going from 21% to 31% is **10 points** higher |

---

## Data

| | File | What it gives | Period |
|---|---|---|---|
| SNAP | `Data/processed/snap_2022_2026_clean.csv` (originals: `Data/SNAP_20XX_RAW.pdf`) | people, households, dollars, by county office and month | Jan 2022 – **Mar 2026** |
| Food shelf | `Data/processed/foodshelf_county_month.csv`, `foodshelf_site_month.csv` | visits, pounds, individuals | Jan 2022 – Jul 2026 |
| Population / poverty | `poverty_2022_2024_clean.csv` (Census ACS 5-year) | residents, people in poverty | 2022–2024 |
| Rural share | `rural_share_2020_clean.csv` (Census 2020) | % of residents living rurally | 2020 |

**Q5 uses Jan 2022 – Mar 2026 (51 months)**, the months where we have both SNAP and food shelf data. SNAP stops in March 2026 because the state publishes about 3 weeks after each month and we must not use anything from August 2026.

**SNAP source for the slide:** MN Department of Human Services, Reports and Forecasts Division, *"Supplemental Nutrition Assistance Program (SNAP) and State-Funded Food: Minnesota Cases, Recipients, and Payments"*. County office × month. Includes Minnesota's state-funded food benefit. We checked the cleaned CSV against the PDFs; spot checks match exactly.

🚨 **Never re-download the 2026 SNAP PDF**: a newer copy may contain August 2026, which disqualifies the team.

---

## Step 1: Getting the data ready

### 1a. SNAP
- **What:** turned month names into real dates; calculated **benefit per person**; matched each SNAP office to a county and gave it a FIPS code.
- **Why:** dates line SNAP up with food shelf months. Benefit per person separates *how much each person gets* from *how many people get it*, two different things.
- **The county problem:** SNAP is run by **county offices**, which don't line up perfectly with Minnesota's 87 counties:
  - **82 counties** have their own office, easy to match.
  - **2 shared offices:** MNPrairie reports Dodge + Steele + Waseca **together**; WPHS reports Grant + Pope **together**. The state doesn't split them, so these 5 counties are left out of county comparisons.
  - **3 tribal nations** run their own SNAP office: White Earth Nation, Red Lake Nation, Mille Lacs Band. Some residents of **7 counties** (Mahnomen, Becker, Clearwater, Beltrami, Mille Lacs, Pine, Aitkin) get SNAP through them, so those counties' SNAP numbers look **too low**. They're left out of county SNAP comparisons. (Same rule as the Q1 notebook.)
- **Why not split the shared offices by population:** that would invent numbers the state never published.

### 1b. Statewide monthly table
- **What:** all of Minnesota added up per month: SNAP people and dollars, food shelf visits, pounds, individuals. 51 rows.
- **Why:** statewide totals avoid the county-office problem entirely; everyone is counted once, including tribal SNAP.

### 1c. County monthly table
- **What:** for the 82 matchable counties, SNAP and food shelf numbers side by side each month, plus population, poverty and rural share.
- **Why:** needed for the county comparisons (Parts A2 and C).

---

## Part A: Together or replace?

**Two possible answers:**
- **Replace:** SNAP goes down → food shelf use goes up (food shelves fill the gap).
- **Together:** both rise and fall together (the same struggling families use both).

### A1. Over time (statewide)
- **What:** a chart of SNAP enrollment and food shelf visits, both starting at 100 in Jan 2022; and the Spearman correlation between their **year-over-year changes**.
- **Why YoY changes:** visits climbed every year while SNAP stayed flat. Raw numbers would only show that. YoY asks: *when SNAP grew faster or slower than usual, did visits follow?*
- **Why not month-to-month changes:** both go up and down with the seasons, which would create a fake "together" link.
- **Found:**
  - March 2022 → March 2026: SNAP enrollment **−3%**, food shelf visits **+92%**, individuals **+99%**.
  - Month-by-month link: rho **−0.06** (visits), **+0.07** (individuals), **+0.15** (pounds), all **≈ 0** (p-values 0.4–0.7).
- **Meaning:** food shelf visits nearly doubled **while SNAP enrollment barely moved**. Food shelf growth came from something other than SNAP enrollment.

### A2. Across counties
- **What:** for 74 counties (2023–24 averages), compared SNAP per 1,000 residents, and SNAP per person in poverty, with food shelf visits per 1,000 residents.
- **Why per 1,000 residents:** removes county size; otherwise Hennepin tops everything.
- **Found:** rho **+0.12** (SNAP per 1,000), **+0.10** (SNAP per poor person), **+0.09** (poverty rate), all weak and not distinguishable from chance (p ≈ 0.3–0.4).
- **Meaning:** counties with more SNAP use have only **slightly** more food shelf use. Not "replace", and only a very weak "together". Poorer counties don't clearly use food shelves more either, which matches Q1.

**Part A answer:** SNAP enrollment and food shelf use **mostly go their separate ways**. Food shelf demand grew for reasons beyond SNAP enrollment.

---

## Part B: What happened when SNAP was cut?

**The event:** during COVID, everyone on SNAP got **extra** money. It **ended in April 2023** (April is the payment month in this data):
- benefit per person: **≈ $260 → $160 a month** (almost −40%)
- people on SNAP also fell **5.7%** that month

**Two problems with a simple before/after:**
1. **Seasons:** visits are always higher in May than March, so "visits rose after April" means nothing.
2. **Visits were already rising** every year before the cut.

**The method: year-over-year windows.** Compare each month with the same month a year earlier, then look at *which two periods* each comparison spans:

| Period | Compares | Growth contains |
|---|---|---|
| Jan–Mar 2023 | boost vs. boost | normal growth only |
| **Apr 2023 – Mar 2024** | **after cut vs. boost** | **normal growth + the cut's effect** |
| Apr 2024 – Mar 2025 | after vs. after | normal growth only |

If the cut pushed people to food shelves, the **middle period should be highest**.

### B1. Month-by-month YoY
- **What:** YoY % change for every month, Jan 2023 – Jul 2026, for visits, pounds and individuals. Chart: `outputs/q5/q5_b1_visits_yoy.png`.

### B2. Average per period (main result)

| Period | Visits | Individuals | Pounds |
|---|---|---|---|
| Jan–Mar 2023 (normal) | +21% | +41% | +20% |
| **Apr 2023 – Mar 2024 (after cut)** | **+31%** | +37% | +19% |
| Apr 2024 – Mar 2025 (normal) | +8% | +9% | +6% |

- **Visits:** growth was highest right after the cut, **about 10 points above** the period before. That's the expected pattern.
- **Individuals and pounds did not jump the same way.** More household trips, but not more food given out, so each visit likely got less food.
- **Timing:** the biggest jump came **Oct 2023 – Feb 2024** (up to +49%), 6–10 months after the cut, not immediately.
- **Why not a regression with a trend line (the original backup plan):** growth wasn't a straight line. It was very fast in 2022–23, then flattened. A straight trend would be wrong, and the "after the cut" switch would soak up that bend and **overstate** the SNAP effect. Comparing periods like-for-like avoids this.

### B3. Double-check: same food shelves only
- **What:** redid visits growth using only food shelves that reported **in both years** (matched sites, about 400–440 food shelves).
- **Why:** if new food shelves joined the data, totals rise for reasons unrelated to SNAP.
- **Found:** **+11% → +31% → +10%**. The middle period stands out even more (about 20 points above both sides). So it isn't caused by food shelves joining or leaving.
- **Weak spot:** the "before" period is only 3 months, because our data starts in Jan 2022 and YoY needs a year earlier.

### B4. The 2025–26 enrollment drop
- People on SNAP fell **≈ 4%** (Nov 2025 – Mar 2026).
- Visits YoY barely changed (+6.3% → +6.8%); individuals rose a bit (+0.5% → +6.1%); pounds −3.7% → +3.4%.
- **Weak evidence:** only 5 months, a small drop, and early 2026 had other shocks (prices, immigration enforcement in the metro). SNAP data stops in March 2026, so we can't follow it further.

**Part B answer:** after SNAP benefits were cut in April 2023, **food shelf visits grew much faster than usual for about a year**, even at the same food shelves, peaking 6–10 months later.

---

## Part C: Did counties that lost more SNAP see bigger jumps?

**Why:** Part B's weakness is that the cut hit **everyone at once**, so something else statewide could explain the jump. But counties didn't lose equally. If the cut was the cause, **bigger loss → bigger jump**, like a bigger medicine dose giving a bigger effect.

### C1. SNAP lost per resident
- **What:** average monthly SNAP dollars in Jan–Mar 2023 minus Apr–Jun 2023, divided by population.
- **Found:** median **$9.43** per resident per month, range $3.11 to $17.78.
- **Why only to June:** October brings a yearly cost-of-living increase, which would mix in a different change.

### C2. Visit growth per county
- **What:** visits in Apr 2023 – Mar 2024 vs. the year before, **matched sites only**; also the next year's growth as each county's "normal".
- **Why matched sites:** county totals jump when a food shelf opens (e.g. Rice County's total doubled).
- **Kept 66 counties.** Dropped: 7 tribal-overlap counties, 5 shared-office counties, Wilkin (no food shelf), and small counties with under 1,000 visits in the base year (one family more or less swings their % wildly).

### C3. The test
- One dot per county: SNAP lost (left → right) vs. visit growth (bottom → top), coloured by rural share. Chart: `outputs/q5/q5_c3_county_dose_response.png`.
- **Found:** rho **+0.01** (p = 0.97). For extra growth (vs. the next year): **−0.01**. **No pattern.**

### C4. As groups

| Counties that lost… | Typical SNAP loss | Typical visit growth |
|---|---|---|
| the least | $6.90 | +34% |
| middle | $9.20 | +26% |
| the most | $12.80 | +31% |

More urban counties (<50% rural) grew **+36%**, more rural ones **+28%**, with the same typical SNAP loss (≈ $9).

**Part C answer:** the jump happened **about equally everywhere**, not more where SNAP losses were bigger. That **weakens** the claim that the cut was *the* cause. Statewide pressures like grocery prices (Q4) fit just as well. It **doesn't rule the cut out**: every SNAP household lost at least $95 a month in every county, so food shelf visitors everywhere felt it. Our county measure mostly reflects how many people are on SNAP, not how hard each household was hit.

---

## Part D: The answer and the message

**Q5 answer:**
1. **Together or replace?** Neither, clearly. SNAP enrollment stayed flat while food shelf visits nearly doubled.
2. **When benefits change?** After the April 2023 cut, visits grew about 10–20 points faster than usual for about a year.
3. **Different by place?** Not much. The jump was similar everywhere; urban counties grew a little more.

**Message for lawmakers:**
> *"When Minnesota's SNAP benefits per person dropped by almost 40% in April 2023, food shelf visits grew much faster than usual for the next year, in every kind of county, even though the number of people on SNAP barely changed. Cutting how much SNAP pays sends households to food shelves that are already at record demand."*

Always with the caveat: other statewide pressures rose at the same time, so the cut is **one important contributor, not the only cause**.

**What The Food Group can do on Monday:**
1. Treat SNAP benefit cuts as an **early warning**: expect more visitors over the **next 6–12 months**.
2. Prepare **everywhere**, not only high-SNAP counties.
3. Track **pounds per household**; visits rose but food didn't.
4. In policy arguments, stress that SNAP benefit **levels** matter, not only eligibility.

**Slide charts (`outputs/q5/`):**
1. `q5_a1_snap_vs_visits_index.png`: SNAP flat, visits climbing
2. ⭐ `q5_b1_visits_yoy.png`: visits grew much faster after the cut
3. `q5_c3_county_dose_response.png`: similar everywhere

---

## Limitations

- **No untouched comparison group:** the cut hit all of Minnesota at once, and other things changed at the same time. We show timing that fits, not proof of cause.
- **Short "before" period** (3 months).
- **SNAP is reported by county office:** 12 counties handled specially.
- **SNAP data ends March 2026**, so the 2025–26 drop is only followed for 5 months.
- **Food shelf data counts where the food shelf is**, not where visitors live.

## Likely judge questions

| Question | Answer |
|---|---|
| *Why not compare March and May 2023 directly?* | Seasons: May is always busier. We compare each month with the same month a year earlier. |
| *Couldn't new food shelves explain the jump?* | We redid it with only food shelves that reported both years; the jump is even clearer (+11% → +31% → +10%). |
| *So did the SNAP cut cause it?* | The timing fits strongly, but counties that lost more didn't jump more, so it's likely one of several statewide pressures. |
| *Why is the SNAP data only to March 2026?* | The state publishes with a lag, and we can't use August 2026 data. |
| *Why leave out some counties?* | Their SNAP is reported jointly or partly through tribal offices, so we don't have a correct county SNAP number for them. |
