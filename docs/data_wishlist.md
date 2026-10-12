# Data wishlist: county factors we do NOT have yet

These would help explain the gap between **need** (Map the Meal Gap food insecurity) and **demand** (food shelf visits) in Q1 and Q6. Each entry says why it matters, where it lives, its grain, and what someone has to do to get it.

**Realistic in 3 days?** ✅ = yes, a few hours · ⚠️ = possible but fiddly · ❌ = no (needs a data request, a long build, or isn't public).

> 🚨 **August 2026 rule.** Many of these pages update monthly. Before downloading anything, check the **last month in the file**. If it includes August 2026 or later, drop those rows **in memory before saving**, or use an archived copy that ends earlier. Never use `snap-dashboard-data-through-september-2026.xlsx`.

## 1. Needs a free Census API key (✅ key obtained; most items done)

> ✅ **Done 2026-10-12** in `notebooks/06b_acs_factors.ipynb` (columns in `county_factors_2022_2024.csv`, sources in `source_register.md` B2): B22003, B25070, B25091, B05002, B03002, B09020, C18130 (+ B09001 child population). Still open: B22001/B22002.

`api.census.gov` now requires a key. Sign up (free, instant by email): **https://api.census.gov/data/key_signup.html**, then set it as an environment variable `CENSUS_API_KEY` and we can add these to `06a_build_county_factors.ipynb` in about an hour. All are ACS 5-year, county, 2018–22 / 2019–23 / 2020–24 (same windows as the poverty file).

| Factor | Why it matters for need vs. demand | ACS table (exact) | Grain |
|---|---|---|---|
| ✅ **SNAP gap**: households in poverty that do *not* get SNAP (`pct_poverty_hh_no_snap`) | Eligible people not using SNAP likely also don't use food shelves (stigma, awareness, paperwork). Directly separates "need" from "help received". | **B22003** (Receipt of SNAP in past 12 months by poverty status, households): `_003E` received & below poverty, `_006E` not received & below poverty (corrected line numbers) | county × 5-yr |
| ✅ Housing cost burden (renters, owners) (`pct_hh_cost_burdened_30`, `pct_hh_severe_burden_50`, by tenure) | High rent leaves less for food → more food shelf demand at the same FI rate. SVI/CHR have versions, but not split by tenure. | **B25070** (gross rent as % of household income), **B25091** (owner costs as % of income, by mortgage status) | county × 5-yr |
| ✅ Foreign-born share, non-citizen share (`pct_foreign_born`, `pct_noncitizen`) | Immigrant fear (public charge) can suppress both SNAP and food shelf use. | **B05002** (place of birth by nativity and citizenship) | county × 5-yr |
| ✅ American Indian / Alaska Native share, by Hispanic origin (`pct_aian_alone`, `pct_hispanic_acs`, `pct_nonwhite`) | Tribal members may use tribal food programs (FDPIR) instead of food shelves. SVI has `pct_aian` (2018–22 only); this gives all 3 windows. | **B03002** (Hispanic or Latino origin by race) | county × 5-yr |
| ✅ Seniors living alone (`pct_65plus_living_alone`, B09020) | Isolated seniors are less likely to get to a food shelf; transport and awareness barrier. | **B09020** (relationship by household type, population 65+: "householder living alone") or **B11007** | county × 5-yr |
| ✅ Disability by poverty (`pct_disabled_in_poverty`) | Mobility limits reduce food shelf visits relative to need. SVI `pct_disability` has it for 2018–22 only, not by poverty. | **C18130** (age by disability status by poverty status) | county × 5-yr |
| SNAP receipt among households with seniors / children | Who is reached by SNAP. | **B22001** (receipt by presence of people 60+), **B22002** (by presence of children) | county × 5-yr |

## 2. Downloadable now, without a key

| Factor | Why it matters | Source and link | Grain | What to do | 3 days? |
|---|---|---|---|---|---|
| ✅ **MN DEED Cost of Living** (obtained 2026-10-12, `06c`; one edition, no year in file; tested in Q1b 8c and Q6 12c: changes nothing) | A family's basic-needs budget differs a lot by county; MMG's cost-per-meal only covers food. Higher cost of living → more demand at the same income. | MN DEED, *Cost of Living in Minnesota* (download "Cost of Living data"): https://mn.gov/deed/data/data-tools/col/ | county (also region), annual | Download the county Excel from the page (manual, may be behind a form). Use the 2022–2024 editions. | ✅ |
| **Free/reduced-price meal eligibility by district** (more detail than CHR) | Child need indicator from a different source than Census. ⚠️ Since 2023-24 MN school meals are universal, so applications may have fallen and eligibility counts may be less reliable. | MDE Data Center, *School Nutrition / Free and Reduced-Price eligibility* (district & school): https://public.education.mn.gov/MDEAnalytics/DataTopic.jsp?TOPICID=1 | school district (needs district → county crosswalk, e.g. NCES EDGE) | Download the "Free/Reduced Priced Meal Eligibility" file, then join districts to counties by enrolment share. | ⚠️ |
| **School meal claims** (the competition's MDE files) | Same idea; meal counts by site. | `Data/MDE School Meal Data/` (competition data) | **site/sponsor only, no county** | Needs MDE's site list with addresses or county (MDE "Site/Sponsor list" in the Data Center), then geocode. Universal meals since 2023-24 blur free vs reduced. | ⚠️ |
| ✅ **SNAP retailer locations** (store list, points) (obtained 2026-10-12, `06c`: counts 1 Jul 2022–2025, closures, distance to nearest full-service store; distance explains Q6 divergence about as well as food shelf distance, nothing for Q1) | Count/density of stores that accept SNAP; finer than CBP (includes small stores with < 3 per county). | USDA FNS, *SNAP Retailer Locator / Historical SNAP Retailer Locator Data*: https://www.fns.usda.gov/snap/retailer/historical-data | point (lat/long, county in file), with authorization/end dates | Download the CSV; count stores active on 1 Jul of each year by county. **Filter out any store-dates ≥ 2026-08.** | ✅ |
| ✅ **WIC participation** (obtained 2026-10-12, `06c`: CY2020–2022 county PDFs, extracted cleanly; 2023–2024 still missing; used to validate the Q6 need index) | Another food-assistance uptake measure (young children); low WIC uptake where need is high hints at access/awareness barriers. | MN Department of Health, *WIC Program data / WIC participation by county*: https://www.health.state.mn.us/people/wic/localagency/reports/index.html | county / WIC local agency, monthly or annual | Download the participation reports (often PDF). Check months (drop ≥ 2026-08). | ⚠️ |
| **Medicaid / MinnesotaCare enrollment** | Enrolment shows how connected low-income people are to public programs; post-2023 "unwinding" disenrolment may push people to food shelves. | MN DHS, *Minnesota Health Care Programs enrollment by county* (dashboard and monthly reports): https://mn.gov/dhs/about-us/forms-resources/reports/ | county, monthly | Download county enrolment; **drop months ≥ 2026-08**. | ⚠️ |
| **Eviction filings** | Housing crisis → sudden food shelf demand. | Eviction Lab (Princeton): https://evictionlab.org/get-the-data/ (county files to 2018; tracking sites for some cities). **MN Housing Partnership / HOME Line** publish MN eviction filings by county from MN Judicial Branch data: https://www.mhponline.org/ (Evictions reports). | county, annual | Eviction Lab county CSV is easy but ends ~2018. MHP reports are PDFs; check for a county table for 2022–2024. | ⚠️ |
| **Broadband (FCC)** | Online awareness/sign-up for food help; CHR uses ACS subscription, FCC gives availability. | FCC National Broadband Map, county summary downloads: https://broadbandmap.fcc.gov/data-download | county / location, semi-annual | Download "Area summary – county" CSV for Jun 2022 / Jun 2023 / Jun 2024. | ✅ |
| **Tribal reservation boundaries** | Tribal nations run their own programs (FDPIR, tribal food shelves) and have their own SNAP agencies in MN (White Earth, Red Lake, Mille Lacs). Our `pct_pop_tribal_area_approx` (from SRAM) misses reservations without Census "tribal subdivisions", e.g. probably **Red Lake** (Beltrami shows only 14%). | Census TIGER/Line *American Indian / Alaska Native / Native Hawaiian Areas* (AIANNH) shapefile: https://www2.census.gov/geo/tiger/TIGER2023/AIANNH/ ; and population by reservation from the 2020 Census (DHC) | polygon → county (overlay with blocks) | Overlay reservation polygons with 2020 block populations (Census block file) to get % of county population living on reservation land. Needs geopandas. | ⚠️ |
| **FDPIR participation** (Food Distribution Program on Indian Reservations) | Tribal members on FDPIR can't also get SNAP; a substitute for food shelf use on reservations. | USDA FNS FDPIR program data (national by state/ITO): https://www.fns.usda.gov/pd/food-distribution-program-indian-reservations-fdpir | tribal organisation, annual | Download; map tribes to counties by hand (only ~7 MN programs). | ⚠️ |
| **MN Compass** county profiles | Ready-made MN indicators (housing, aging, immigration, disability). Mostly ACS repackaged, but handy for checking ours. | Wilder Research, MN Compass: https://www.mncompass.org/data-insights/county-profiles | county | Manual download per indicator. | ✅ (for spot checks) |

## 3. Hard to get or not public at county level

| Factor | Why it matters | Source | Problem | 3 days? |
|---|---|---|---|---|
| **211 calls for food help** | Direct measure of people *looking* for food help (awareness, demand). | United Way 211 (MN): https://www.211unitedway.org/ ; 211 Counts dashboards: https://211counts.org/ | County-level call data usually needs a data request; MN may not be on 211 Counts. | ❌ |
| **Food insecurity among seniors** | Seniors under-use food shelves relative to need (stigma, mobility). | Feeding America, *The State of Senior Hunger* (state-level; county not published); Elevating Voices (qualitative): https://www.feedingamerica.org/research | State-level only; no county estimates. | ❌ |
| **Stigma / awareness surveys** | Explain why need doesn't turn into visits. | Feeding America *Elevating Voices*, Hunger Solutions MN / Second Harvest Heartland "Make Hunger History" surveys | Not county-level, mostly reports. Use as qualitative support only. | ❌ (cite qualitatively) |
| **ACS 1-year** county estimates | Year-specific ACS. | Census API | Only counties ≥ 65,000 people (~11 of 87 MN counties). Use SAIPE instead (done). | — |
| **Food bank partner-agency hours / capacity** | Supply side: open hours limit visits. | Food banks (Second Harvest Heartland, Northland, etc.) | Ask organisers / food banks. | ❌ |

## 4. Small things to improve in what we already have

- **CBP 2024** (`cbp24co.zip`) is not released yet (404 on 2026-10-11). When it is, re-run 06a to fill the 2024 store counts.
- **CBP < 3 rule:** grocery store counts are blank in 17–18 small counties. ✅ The SNAP retailer list now gives exact counts (`county_extra_factors.csv`).
- **WIC 2023–2024:** the MDH county PDFs we have stop at CY2022; newer years would let WIC be compared with food shelf data for all of 2022–2024.
- **SVI / CHR are one vintage.** If year-varying versions are needed, SVI 2020 (ACS 2016–20) and CHR 2023/2024 releases are on the same pages.
