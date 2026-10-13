---
editor_options: 
  markdown: 
    wrap: 72
---

# 04 · Q4: Food prices and food shelf activity, explained

Companion to `notebooks/04_q4_prices_foodshelf.ipynb`. The notebook has
the code and short notes. This file explains **every step in plain
language**: what we did, why, what we found, and why we didn't do it
another way. Read it before presenting Q4.

Charts: `outputs/q4/`. Price data:
`Data/processed/cpi_monthly_2019_2026.csv` (source notes in
`Data/external/bls_cpi/README.md`).

------------------------------------------------------------------------

## The question

The brief asks:

1.  Do more people come to food shelves **when grocery prices rise**?
2.  Does the response happen **at once, or after a delay**?
3.  Does it show up in **all three metrics** (visits, individuals,
    pounds)?
4.  Are there **other repeating patterns** that prices don't explain?

Why it matters: if the delay is known, The Food Group can tell food
shelves *"expect more people in N months"* and tell donors *"need will
rise next year"* **before** it happens.

## The short answer

| Question | Answer |
|------------------------------------|------------------------------------|
| More people when prices rise? | **Yes, probably**, but the evidence rests on **one** inflation episode (2021–23) and overlaps with the SNAP cut. |
| At once or delayed? | **Delayed.** No same-month response. Food shelf growth lines up best with grocery inflation **about 15 months earlier** (likely range **12–17 months**; 95% range 12–20). |
| All three metrics? | **Yes, all three**, with the same delay. **Individuals** follow prices most closely; **pounds** grew least (pounds per visit fell from 61 lb to 50 lb); **visits** share the most credit with the SNAP cut. |
| Other patterns? | **Yes**: August and Oct–Nov are busiest, December lowest; longer months (more weekdays) are busier; one-off shocks (Jan 2026 enforcement period) are not price-driven. |

**Message for food shelves and donors:** \> *"When grocery prices start
rising faster, food shelves feel it about a year later, not right away.
Demand starts to climb about 6 months after a price surge and peaks
about 12–17 months after it. That year is the time to raise money and
stock up."*

------------------------------------------------------------------------

## Words used in this document

| Term | Meaning |
|------------------------------------|------------------------------------|
| **CPI** | Consumer Price Index: the government's measure of prices. **Food at home** = groceries (not restaurants). |
| **Inflation** | how fast prices are rising: % change in the CPI vs the **same month a year earlier** |
| **Disinflation vs deflation** | disinflation = prices still rise, just more slowly (what happened after 2022). Deflation = prices actually fall (never happened here). |
| **YoY (year-over-year) growth** | a month vs the same month a year earlier. Removes seasons. |
| **Matched sites** | only food shelves that reported in **both** months being compared, so food shelves joining or leaving can't change the result |
| **Lag / delay** | how many months after a price change food shelves feel it |
| **Correlation** | −1 to +1: do two things rise and fall together? 0 = no pattern |
| **p-value** | roughly, how often a pattern this strong would appear **by pure chance**. Small (≤ 0.05) = probably real |
| **Surrogate ("fake") series** | a made-up inflation series with the same smoothness as the real one but its rises and falls at **random times**. Used to measure what "chance" looks like. |
| **Bootstrap** | re-running the analysis many times on reshuffled blocks of months, to see how much the answer could wobble |
| **Regression coefficient (b)** | "if inflation is 1 point higher, food shelf growth is b points higher" |
| **AIC / BIC** | standard scores for choosing between models; they reward fit but **penalise** extra complexity. Lower = better. |
| **Cross-validation** | fit the model without one year, predict that year, repeat. Good choices predict unseen years well. |
| **Newey–West (HAC) standard errors** | error bars that allow neighbouring months to be similar (ordinary error bars would be too narrow) |
| **STL** | a standard method that splits a series into **trend + season + leftover** |
| **Seasonal index** | a month's value ÷ its 12-month average × 100. 105 = 5% busier than a typical month |

------------------------------------------------------------------------

## Data

|   | File | What it gives | Period |
|------------------|------------------|------------------|------------------|
| Grocery prices | `Data/processed/cpi_monthly_2019_2026.csv` (cache: `Data/external/bls_cpi/`) | CPI index levels and YoY inflation, 11 series | Jan 2019 – **Jul 2026** |
| Food shelf | `foodshelf_county_month.csv`, `foodshelf_site_month.csv` | visits, individuals, pounds, children (meal programs excluded) | Jan 2022 – Jul 2026 |
| SNAP | `snap_2022_2026_clean.csv` (statewide sum) | benefit per person | Jan 2022 – Mar 2026 |
| County traits | `rural_share_2020_clean.csv`, `poverty_2022_2024_clean.csv`, `mmg_mn_county_2022_2024.csv` | \% rural, poverty rate, % food-insecure above SNAP limit | 2020 / 2024 |

🚨 **August 2026 rule.** The BLS website already has August 2026 prices.
We dropped every month after July 2026 **in memory, before saving
anything** (10 values dropped), and the notebook stops with an error if
any later month appears (`assert date.max() <= 2026-07-01`).

### Source documentation (BLS CPI)

| Item | Primary series | Robustness / comparison series |
|------------------------|------------------------|------------------------|
| **1. Publisher + exact series** | U.S. Bureau of Labor Statistics, CPI-U, **`CUUR0200SAF11` Food at home, Midwest region, not seasonally adjusted** (index 1982–84 = 100) | `CUUR0000SAF11` / `CUSR0000SAF11` U.S. food at home (NSA / SA); `CUURS24ASAF11` Minneapolis–St. Paul food at home; `CUUR0200SA0` Midwest all items; `CUUR0200SEFV` Midwest food away from home; `CUUR0200SAH1` shelter, `CUUR0200SETB01` gasoline, `CUUR0200SA0E` energy (Midwest); `CUURS24ASA0` Minneapolis–St. Paul all items |
| **2. Geographic grain** | Midwest Census region (12 states including Minnesota); one number for the whole state | U.S.; Minneapolis–St. Paul–Bloomington metro |
| **3. Time grain** | monthly | monthly (Minneapolis–St. Paul *all items*: **every other month**) |
| **4. Why chosen** | It measures **groceries** specifically (what food shelf visitors would otherwise buy), it's **monthly** (needed to measure a delay in months), and Minnesota is in the region. | **Minneapolis–St. Paul**: more local, but built from a much smaller price sample (noisier), covers only the metro while food shelves are statewide, and its all-items index is bimonthly. **U.S.**: less specific to Minnesota. **All items**: includes housing, gas, etc., not just food. We ran all of them as checks; the delay is the same. |
| **Publication lag** | Each month's CPI is released around the **middle of the following month** (July 2026 CPI ≈ mid-August 2026). So in practice The Food Group would know a month's grocery inflation \~2 weeks after the month ends. | same |
| **Access** | BLS Public Data API v2 (no key), fetched once on 2026-10-11 | same call |

**One gap:** **October 2025** prices were never collected (federal
government shutdown). We filled it with the midpoint of September and
November and flagged it (`oct2025_imputed`). It affects one month out of
91.

------------------------------------------------------------------------

## Step 0: What prices did (2019–2026)

-   Midwest grocery inflation rose from \~0% (spring 2021) to a **peak
    of 15.2% in August 2022**, then slowed to **1–3%** from late 2023
    on.
-   Grocery prices **never fell**: they are **28.5% higher** in Jul 2026
    than in Jan 2021, and there was **not a single month** of lower
    prices than a year earlier.
-   So our data contain **one speed-up and one slow-down** in price
    growth, not prices going up and back down. Every finding is about
    **how fast prices rise**, and rests essentially on this one episode.

------------------------------------------------------------------------

## Step 1: The statewide monthly table

-   **What:** one row per month (Jan 2022 – Jul 2026, 55 months):
    visits, individuals, pounds, children; number of reporting food
    shelves; inflation (11 series); SNAP benefit per person; and a
    "SNAP-cut window" marker.
-   **Three versions of each food shelf metric:**
    1.  **All sites:** statewide total.
    2.  **Per reporting site:** total ÷ food shelves that reported that
        month.
    3.  **Matched sites (main):** YoY growth using only food shelves
        that reported in **both** months (391–447 food shelves per
        month).
-   **Why matched sites are the main version:** the food shelf network
    changed over time. If new food shelves join, totals rise even if no
    extra family is hungry. Matched sites remove that (same rule as Q5).
-   **Why YoY on both sides:** food shelf use and prices both have
    seasons, and both trend upward. Comparing *levels* would show a fake
    link (prices only rose, visits only rose → "perfect" correlation
    that means nothing). Comparing *rates of change* asks the right
    question: when prices rose **faster**, did food shelf use grow
    **faster**?
-   **Usable months:** YoY growth needs a year of history, so food shelf
    growth exists **Jan 2023 – Jul 2026 (43 months)**. Inflation goes
    back to 2020, so we can look up to 24 months back.

------------------------------------------------------------------------

## Step 2: The picture

Chart: `outputs/q4/q4_1_inflation_vs_growth.png` ⭐

-   Inflation peaked in **Aug 2022**. Food shelf growth (same food
    shelves) stayed very high through 2023 and peaked in **Jan–Feb
    2024** (+44% / +49%), **about 18 months later**, then fell to single
    digits in 2025 while inflation sat at 1–3%.
-   **No jump at the moment prices spiked.**
-   **Caution:** both lines just "go up then down" **once**, and the
    SNAP cut (Apr 2023) lands in between. The eye can be fooled, so
    Steps 3–4 test this properly.
-   Feb 2024's +49% is partly a quirk: Feb 2023 visits were unusually
    low (Feb 2022 looks over-reported).

------------------------------------------------------------------------

## Step 3: The lag profile, against chance

Chart: `outputs/q4/q4_2_lag_profile.png`

-   **What:** for each delay from 0 to 24 months, the correlation
    between food shelf growth this month and grocery inflation that many
    months earlier.
-   **Why a special "chance" test:** YoY numbers overlap (Feb and Mar
    share 11 of 12 months), so neighbouring months are near-copies.
    **Any two smooth hump-shaped series correlate strongly at *some*
    delay.** So we made **2,000 fake inflation series** with the same
    smoothness but humps at random times, ran the **whole** lag search
    on each, and recorded the **best** correlation each fake series
    could get. The real result has to beat that. Because the fake series
    also get to pick their best of 25 delays, **"picking the best lag"
    is already paid for** in the test.

|   | Visits | Individuals | Pounds |
|------------------|------------------|------------------|------------------|
| Correlation, **same month** (lag 0) | −0.06 | +0.19 | +0.10 |
| Correlation, lag 6 | 0.33 | 0.53 | 0.42 |
| Correlation, lag 12 | 0.73 | 0.85 | 0.76 |
| **Best lag** | **15** | **15** | **15** |
| Correlation at best lag | 0.78 | 0.89 | 0.83 |
| Chance threshold (95%, best of 25 lags) | 0.79 | 0.87 | 0.82 |
| **p-value (incl. picking the lag)** | 0.06 | **0.008** | **0.016** |
| Best lag, bootstrap 80% range (95%) | 12–17 (12–20) | 12–16 (12–17) | 14–17 (12–17) |

-   **Same-month correlation ≈ 0.** No immediate response.
-   The match grows steadily from lag 0 to a **peak at 15 months** and
    fades by \~24 months.
-   Individuals and pounds beat chance; visits are just short (p =
    0.06).
-   **Placebo, time running backwards:** *future* inflation (1–12 months
    ahead) does **not** line up (best correlation −0.10 to +0.13). Good:
    the order of events is right.
-   **Placebo, other prices:** this is the honest catch. **All-items**
    inflation lines up just as well (lag 18, correlation 0.79, p =
    0.02), and so does shelter (lag 5, it peaked a year later).
    Groceries, rent, gas and everything else surged together in 2021–23.
    **The data cannot tell grocery prices apart from the general
    cost-of-living squeeze**, so we say "rising prices, led by
    groceries", not "grocery prices alone".

**Why not just eyeball the delay?** See "The teammate's question" below.

------------------------------------------------------------------------

## Step 4: Regression, with a pre-stated rule for the delay and SNAP as a control

**Model:**
`food shelf YoY growth = a + b × grocery inflation k months earlier (+ c × SNAP-cut window) + error`

-   **SNAP-cut window:** 1 for Apr 2023 – Mar 2024, the months whose YoY
    comparison straddles the end of SNAP emergency allotments (Q5). A
    second version uses the YoY % change in SNAP benefit per person.
-   **Error bars:** Newey–West (allow 12 months of overlap between
    neighbouring months).
-   **How the delay was chosen, decided before looking:**
    1.  always report the pre-set delays **0, 3, 6, 12**;
    2.  choose k from 0–24 by **AIC** and **BIC**;
    3.  **leave-one-year-out cross-validation** (fit on three years,
        predict the fourth).

### The confounding problem, in one number

The SNAP-cut window and grocery inflation 12 months earlier have a
correlation of **0.87** (15 months earlier: 0.83). The price spike
(spring–autumn 2022) came about a year before the SNAP cut's effect
window (Apr 2023 – Mar 2024). With one episode, **the data cannot
cleanly split credit between them**, so we show both models.

### Results

| Metric | Delay chosen (AIC / BIC / CV), no SNAP control | b, no SNAP control | Delay chosen, with SNAP control | b, with SNAP control | SNAP window effect |
|------------|------------|------------|------------|------------|------------|
| Visits | 15 / 15 / 15 | **2.1** (1.6 to 2.6) | 17 / 17 / 23 | **1.2** (0.7 to 1.8) | +13.5 pts (p \< 0.01) |
| Individuals | 15 / 15 / 15 | **2.9** (2.7 to 3.1) | 15 / 15 / 14 | **2.8** (1.5 to 4.2) | +0.9 pts (p = 0.9) |
| Pounds | 15 / 15 / 16 | **1.6** (1.4 to 1.8) | 15 / 15 / 15 | **1.8** (1.4 to 2.3) | −3.1 pts (p = 0.3) |

-   **All three rules pick about 15 months.** The pre-set short delays
    (0, 3, 6 months) are never significant once SNAP is in.
-   **How to read b:** each 1 point of grocery inflation \~15 months
    earlier goes with about **1.2–2.9 points** more food shelf growth at
    the same food shelves. In 2022, inflation was \~11 points above
    normal → roughly +13 to +32 points of extra growth in 2023–24.
-   **Treat the size as an upper bound.** The price spike also coincided
    with the end of other pandemic help (expanded child tax credit ended
    Dec 2021, pandemic school-meal waivers ended mid-2022) and with food
    shelf use recovering after COVID. The model can't separate these.
-   **With the SNAP control:** individuals and pounds keep their
    **full** price effect, and the SNAP window adds nothing for them.
    Visits keep **about half** (2.1 → 1.2; at lag 12: 1.9 → 0.8, p =
    0.06). Using SNAP benefit per person instead of the window gives the
    same picture (visits b ≈ 1.0–1.3, p \< 0.01; a 40% benefit cut ≈ +13
    points of visit growth).

### Step 4b: Any quick (0–3 month) response?

-   **What:** month-to-month % change (per reporting site) on inflation
    in the last 0–2, 3–5, 6–8 and 9–11 months, with month-of-year
    dummies (seasons) and the SNAP window.
-   **Found:** BIC keeps **no** inflation terms for any metric;
    together, the last 12 months of inflation add nothing (p = 0.95
    visits, 0.12 individuals, 0.84 pounds).
-   **Meaning:** no sign of a quick response. Month-to-month data are
    noisy, so this can't rule out a small quick effect, but it can't
    find one.

------------------------------------------------------------------------

## Step 5: Do all three metrics respond?

|   | Visits | Individuals | Pounds |
|------------------|------------------|------------------|------------------|
| Avg YoY growth (same food shelves): 2023 / 2024 / 2025 / 2026 | +23% / +18% / +7% / 0% | +32% / +21% / +2% / +3% | +16% / +13% / −1% / +3% |
| Best lag | 15 | 15 | 15 |
| Correlation at best lag | 0.78 | **0.89** | 0.83 |
| b at lag 12, no SNAP → with SNAP | 1.9 → 0.8 | 2.7 → 2.7 | 1.5 → 1.6 |

-   **Yes, all three respond**, with the **same delay**.
-   **Individuals** track prices most closely, and the effect doesn't
    depend on the SNAP control.
-   **Pounds** grew least. **Pounds per visit fell from ≈61 lb (2022) to
    ≈50 lb (2025–26).** Pounds depend on what food shelves *have* to
    give (food bank stock, donations, federal TEFAP food), so pounds
    measure **supply** as well as demand. When more people came, each
    visit got less food.
-   **Visits** carry the SNAP-cut signal most (same as Q5): the price
    effect for visits halves with the SNAP control.
-   **Message:** treat visits and individuals as the **demand** signal
    and pounds as the **supply** signal. A gap between them is an early
    warning that food shelves are stretching their stock.

------------------------------------------------------------------------

## Step 6: Other patterns prices don't explain

Prices change slowly (over many months), so they can't explain
month-to-month swings. We measured those on **per-reporting-site**
values (removes network growth).

Chart: `outputs/q4/q4_3_seasonal_profile.png`

| Month                  | Jan | Feb | Mar | Apr | May | Jun | Jul | **Aug** | Sep | **Oct** | Nov | **Dec** |
|------|------|------|------|------|------|------|------|------|------|------|------|------|
| Visits (100 = typical) | 98  | 97  | 100 | 102 | 100 | 99  | 102 | **105** | 99  | **103** | 102 | **92**  |
| Individuals            | 100 | 96  | 102 | 102 | 99  | 98  | 100 | 104     | 97  | 103     | 103 | 91      |
| Pounds                 | 99  | 93  | 99  | 99  | 100 | 97  | 100 | 106     | 96  | 105     | 105 | 99      |

1.  **August is the busiest month** (≈5% above normal). The **children's
    share** of people served is highest in Jul–Aug (36.7% in Aug vs
    ≈35.3% in Sep–Nov): school meals stop in summer. **September dips**
    when school meals restart.
2.  **October–November are high** (holiday season, heating costs start).
3.  **December is the lowest month for visits and individuals** (≈8%
    below normal) even though it has a normal number of weekdays:
    holiday closures, and families get help from holiday programs
    elsewhere. **Pounds barely drop in December** (99): holiday
    distributions are bigger per visit.
4.  **Calendar length matters:** each extra weekday in a month adds **≈3
    index points** (all three metrics, p \< 0.01). **February's dip is
    mostly because it's short.**
5.  **One-off shocks** (STL leftovers, not price-related):
    -   Feb 2023 visits −31% (a reporting quirk: Feb 2022 visits look
        too high).
    -   Dec 2023 – Feb 2024 +14 to +25%: the peak of the post-SNAP-cut /
        high-price surge.
    -   **Jan 2026 individuals −22%**, then a Feb–Mar 2026 rebound: the
        early-2026 metro immigration-enforcement period (families may
        have avoided going out).

-   **Why not use the month-of-year from the raw totals:** network
    growth inflates later months; per-site values avoid that.
-   **Why not more years:** we only have 3–4 of each calendar month, so
    a single odd year moves the index by a point or two. Treat
    differences under \~2 points as noise.

------------------------------------------------------------------------

## Step 7: Robustness

| Check | Visits: best lag / b with SNAP (p) | Individuals | Pounds |
|------------------|------------------|------------------|------------------|
| **Base** (matched sites, Midwest food at home) | 15 / 0.77 (0.06) | 15 / 2.73 (\<0.001) | 15 / 1.64 (\<0.001) |
| All sites (raw totals) | 14 / 1.53 (\<0.001) | 12 / 3.63 (\<0.001) | 14 / 2.28 (\<0.001) |
| Per reporting site | 17 / −0.16 (0.79) | 17 / 1.73 (0.001) | 18 / 0.63 (0.29) |
| U.S. food-at-home prices | 14 / 1.01 (0.04) | 14 / 3.40 (\<0.001) | 15 / 2.05 (\<0.001) |
| Minneapolis–St. Paul food at home | 13 / 0.49 (0.28) | 13 / 2.53 (\<0.001) | 13 / 1.46 (\<0.001) |
| Midwest **all-items** prices | 18 / 0.16 (0.80) | 18 / 2.83 (0.008) | 19 / 1.53 (0.004) |
| Drop flagged rows | 15 / 0.96 (0.009) | 15 / 2.78 (\<0.001) | 15 / 1.65 (\<0.001) |
| Food-shelf sites only (no outreach) | 15 / 0.76 (0.10) | 15 / 2.79 (\<0.001) | 15 / 1.66 (\<0.001) |
| 2024–26 only (drops 2023, compared with post-COVID 2022) | 12 (corr 0.81) | 12 (0.89) | 12 (0.81) |

**Reading:** - **The delay survives everything:** 12–19 months in every
version, never 0–6. - **The size with the SNAP control is solid for
individuals and pounds**, but **fragile for visits** (p from \<0.01 to
0.8 depending on the version). - **Bottom line:** the **timing** is
robust; the claim that prices raised **visits** *beyond* what the SNAP
cut did is not.

------------------------------------------------------------------------

## Step 8: Do some counties respond more?

-   **What:** county × month panel (83 counties, 3,263 county-months,
    matched sites), with county and month fixed effects, testing whether
    the price response is bigger in some kinds of counties.
-   **Important limit:** prices are **one statewide number**, so the
    county panel **cannot measure the price effect itself** (month fixed
    effects absorb it). It only tests **differences** between counties.

| County trait (1 standard deviation higher) | Extra response per 1 pt inflation | p |
|------------------------|------------------------|------------------------|
| \% rural | +0.05 (−0.60 to 0.70) | 0.87 |
| Poverty rate | −0.95 (−2.00 to 0.11) | 0.08 |
| \% of food-insecure people earning **too much for SNAP** | +0.97 (−0.05 to 1.98) | 0.06 |

-   **Rural and urban counties respond the same.**
-   **Suggestive only (p ≈ 0.06):** counties where more food-insecure
    people earn too much for SNAP respond a bit **more** to prices. That
    makes sense, since those households have no SNAP to cushion higher
    grocery bills. Worth one sentence, not a headline.

------------------------------------------------------------------------

## Step 9: The answer and the recommended lead time

1.  **Do more people come when prices rise?** Yes, probably: all three
    metrics grew fastest about a year after the 2022 price surge and
    slowed as inflation cooled. Rising prices are one of the drivers,
    along with the SNAP cut and the end of other pandemic help.
2.  **At once or delayed?** **Delayed.** No same-month response; best
    match ≈ **15 months** after inflation.
3.  **All three metrics?** Yes. Individuals most clearly, pounds least
    (supply-limited), and visits share credit with the SNAP cut.
4.  **Other patterns?** August and Oct–Nov busiest, December lowest,
    longer months busier, plus one-off non-price shocks.

### Recommended lead time to communicate

| When grocery (or overall) inflation rises noticeably… | Tell food shelves / donors |
|------------------------------------|------------------------------------|
| **0–5 months later** | no change expected yet: the time to **plan and fundraise** |
| **\~6 months later** | demand starts to climb |
| **\~12–17 months later** (best estimate 15) | **peak pressure** |
| **\~2 years later** | effect has faded, if inflation has calmed |

**Uncertainty:** the 80% range for the peak delay is **12–17 months**
(95%: 12–20). It comes from **one** inflation episode, so treat it as
**"about a year, give or take a season"**, not an exact month.

**What it says about the coming year (using only data through July
2026):** grocery inflation has stayed near **2%** through July 2026
(similar to late 2025), so **groceries alone point to no new surge in
2027**. The watch item is **overall prices**: Midwest all-items
inflation rose from 2.4% (Jan 2026) to **5.0% (May 2026)** on a gasoline
spike (+45% YoY). All-items inflation lined up with food shelf growth as
well as groceries did, so if it stays high, warn food shelves and donors
to expect **above-normal growth from roughly mid-2027**.

**What The Food Group can do on Monday:** 1. Track Midwest food-at-home
and all-items CPI **each month** (free, released mid-month) as an
**early-warning indicator** with a \~1-year lead. 2. Fundraise and
secure food **in the year after** a price surge, before the peak
arrives. 3. Plan for **August and October–November** peaks and the
December dip every year, on top of any price effect. 4. Watch **pounds
per visit**: if it falls while visits rise, food shelves are rationing.

**Slide charts:** 1. ⭐ `q4_1_inflation_vs_growth.png`: price surge in
2022, food shelf surge \~18 months later 2. `q4_2_lag_profile.png`: the
delay is about a year, not immediate 3. `q4_3_seasonal_profile.png`:
seasons that prices don't explain

------------------------------------------------------------------------

## The teammate's question: "Use the SNAP cut to measure how long the 3 metrics take to spike. How long a delay should we take, or is there an issue?"

Good instinct to measure the delay, but four issues with doing it that
way:

**(a) The SNAP cut is a SNAP shock, not a price shock.** Q4 asks about
**prices**. The April 2023 SNAP cut changed how much money families had,
not what groceries cost. Measuring the delay after the SNAP cut answers
Q5 (we did: peak 6–10 months later), not Q4. Q4 needs **variation in
prices**, which is why we used the BLS CPI.

**(b) The SNAP cut and high food prices overlap, so they must be
modelled together.** Grocery inflation peaked in Aug 2022 and was still
7–12% when the SNAP cut hit (spring 2023). The SNAP-cut window
correlates **0.87** with inflation a year earlier. If you measure a
"spike after the SNAP cut", part of it is the price surge, and vice
versa. That's why the regression includes **both**, and why we report
the price effect as a **range** (with and without the SNAP control).

**(c) Don't choose the delay by eye or by picking the best of many.**
With 43 usable months, trying delays of 1, 2, 3 … 24 months and picking
the one that looks best will **always** find something. That's the
"forking paths" / overfitting problem: with enough tries, chance alone
produces a good-looking match. What we did instead: - **pre-set delays**
(0, 3, 6, 12) reported regardless of results; - delay chosen by a
**rule** (AIC, BIC, cross-validation), not by eye: all three agree on
≈15 months; - the result is tested against a **chance benchmark that
also gets to pick its best delay** (2,000 fake inflation series), plus a
**placebo** (future inflation, which does not match) and a **bootstrap**
range for the delay (12–17 months).

**(d) Trending series give fake correlations, so use rates of change.**
Prices only went up and visits only went up from 2022 to 2026, so their
*levels* correlate almost perfectly for no real reason. We compare
**inflation (how fast prices rise) with growth (how fast food shelf use
rises)**. And remember: prices **never fell**. After 2022 they rose
**more slowly** (disinflation), not less (deflation). So we can't say
"visits fall when prices fall"; we can only say "visit growth slows when
price growth slows".

**So what delay should we use?** About **12–17 months from a rise in
grocery inflation to peak food shelf pressure** (best estimate 15), with
demand starting to rise \~6 months in. Say "about a year", not an exact
month.

------------------------------------------------------------------------

## Limitations

-   **Essentially one inflation episode** (2021–23). Everything rests on
    one rise and fall; a second episode could show a different delay.
-   **Only 43 months** of YoY growth, which overlap heavily (that's why
    we used surrogates, bootstrap and Newey–West error bars).
-   **Confounding:** the price surge overlapped with the SNAP cut (Apr
    2023), the end of other pandemic help (child tax credit, school-meal
    waivers), and post-COVID recovery of food shelf use. The size of the
    price effect is an **upper bound**.
-   **Groceries vs everything else:** all-items, shelter and gas prices
    rose at the same time; the data can't isolate grocery prices.
-   **Network growth:** handled with matched sites, but per-site and
    total versions give somewhat different sizes for visits.
-   **Prices are regional** (Midwest), not Minnesota-specific; the
    Minneapolis–St. Paul series gives the same delay.
-   **2026 shocks:** the metro immigration-enforcement period (early
    2026) and a gasoline spike affect the last months.
-   **Seasonal profile** rests on 3–4 years per month.
-   **Food shelf data count where the food shelf is**, not where
    visitors live.

## Likely judge questions

| Question | Answer |
|------------------------------------|------------------------------------|
| *Why not compare price levels with visit levels?* | Both only went up, so they'd correlate almost perfectly for no reason. We compare inflation with growth. |
| *Isn't a 15-month delay suspiciously long?* | It's when the **growth** peaks, not when the effect starts (that's \~6 months). Families first use savings, credit and family help; food shelf use climbs as those run out. The SNAP cut also arrived \~8 months after the price peak. |
| *Couldn't you find a match at some lag by luck?* | Yes, which is why we tested against 2,000 fake inflation series that also got to choose their best lag. Individuals (p = 0.008) and pounds (p = 0.016) beat that; visits are borderline (p = 0.06). |
| *Isn't this just the SNAP cut?* | Partly, for visits. With the SNAP cut in the model, individuals and pounds keep their full price effect; visits keep about half. |
| *Why Midwest and not Minneapolis prices?* | Monthly, bigger sample, statewide relevance. Minneapolis–St. Paul gives the same delay (13 months). |
| *Did prices ever fall?* | No. Grocery prices are 28.5% higher than in Jan 2021. After 2022 they just rose more slowly. |
| *Why do pounds respond less?* | Pounds depend on food supply; pounds per visit fell from 61 to 50 lb, so food shelves stretched supply. |
| *Can you use August 2026 prices?* | No. They exist, but we dropped them before saving and the notebook checks this. |
