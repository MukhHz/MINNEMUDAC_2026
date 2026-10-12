# BLS Consumer Price Index (CPI-U), Jan 2019 – Jul 2026

> 🚨 **CUTOFF RULE: only months up to and including July 2026 are allowed.** The BLS API already returns August 2026 (and will return later months). Using any August 2026+ data from any source disqualifies the team. When fetching, **drop months after 2026-07 in memory before writing anything to disk**, and keep `assert date.max() <= 2026-07-01` in any code that reads prices. The file here was saved that way (10 August-2026 values were dropped before saving).

| | |
|---|---|
| File | `bls_cpi_2019_2026_through_jul2026.json` (filtered API response: series ID, year, month, value) |
| Publisher | U.S. Bureau of Labor Statistics (BLS), Consumer Price Index for All Urban Consumers (CPI-U) |
| Fetched | 2026-10-11, one call to the BLS Public Data API v2 (`https://api.bls.gov/publicAPI/v2/timeseries/data/`, no key), startyear 2019, endyear 2026 |
| Made into | `Data/processed/cpi_monthly_2019_2026.csv` by `notebooks/04_q4_prices_foodshelf.ipynb` (`FETCH = False`: the notebook reads this cache and does not call the API) |
| Publication lag | each month's CPI is released around the **middle of the following month** (e.g. July 2026 CPI ≈ mid-August 2026) |

| Series ID | Meaning | Geography | Frequency |
|---|---|---|---|
| `CUUR0200SAF11` | **Food at home** (groceries), not seasonally adjusted. **Q4 primary.** | Midwest region (12 states incl. MN) | monthly |
| `CUUR0000SAF11` / `CUSR0000SAF11` | Food at home, NSA / seasonally adjusted | U.S. city average | monthly |
| `CUURS24ASAF11` | Food at home | Minneapolis–St. Paul–Bloomington metro | monthly |
| `CUUR0200SEFV` | Food away from home (restaurants) | Midwest | monthly |
| `CUUR0200SA0` / `CUUR0000SA0` | All items | Midwest / U.S. | monthly |
| `CUUR0200SAH1` | Shelter | Midwest | monthly |
| `CUUR0200SETB01` | Gasoline (all types) | Midwest | monthly |
| `CUUR0200SA0E` | Energy | Midwest | monthly |
| `CUURS24ASA0` | All items | Minneapolis–St. Paul | **every other month** (odd months) |

**Missing value:** October 2025 is `-` (not published) for every series except gasoline, because the federal government shutdown stopped BLS price collection. The notebook fills it with the geometric midpoint of Sep and Nov 2025 and flags it (`oct2025_imputed`).

**Why Midwest food at home is the primary series:** it is monthly and covers groceries specifically, and Minnesota is in the Midwest region. The Minneapolis–St. Paul series is more local but built from a much smaller price sample (noisier) and covers only the metro, while food shelves are statewide. The Minneapolis–St. Paul *all items* index is only published every other month. The U.S. series is less specific to Minnesota. All are used as robustness checks.
