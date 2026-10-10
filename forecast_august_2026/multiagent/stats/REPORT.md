# Statistical / local univariate models — August 2026 study

Run: `python forecast_august_2026/multiagent/stats/run.py` (about 150 s). Code: `models.py`, `run.py`. Outputs are in `results/`: `predictions.csv`, `summary.csv`, `cutoff_check.txt`, `fallbacks.csv`, `damped_auto_selections.csv`, `tables.md`. The shared harness was not modified. The two reference baselines run in the same output for comparison.

## What I tried (37 models, all reported below)
- **statsforecast (v2.1.1), season 12, one step ahead:** AutoETS on logs and on levels, AutoARIMA (log), AutoTheta (log), AutoCES (log), MSTL with an ETS trend (log). With fewer than 24 observations these models fall back to seasonal naive. That happens only in the **Aug 2023 fold (n=19)**, so all six of these models have the seasonal-naive APE in their 2023 column. The fallbacks are recorded in `fallbacks.csv`.
- **YoY log-ratio models.** Each forecasts r_t = log(y_t / y_{t-12}) and then sets y_hat = y_{t-12}·exp(r_hat). Variants: SES (`ratio_ses`), AutoETS non-seasonal (`ratio_ets_auto`, which picked the same model as SES), non-seasonal AutoARIMA, AutoTheta, and a fixed rule of half the mean of the last 3 ratios (`ratio_mean3_half`).
- **Damped-YoY grid, fixed a priori:** window w ∈ {1,3,6,12} × damping d ∈ {0.25,0.5,0.75,1.0}, 16 variants. `dyoy_w3_d0.5` is identical to the `damped_yoy_3m` baseline. The w=12 variants cannot be computed for Aug 2023 because they need 24 months; that cell is a recorded failure (NaN), so their aug_mape covers 2024–25 only.
- **`damped_yoy_auto`:** picks (w, d), with d=0 allowed, inside the model. It uses the inner one-step MAPE over the 12 origins before the cutoff and only data before each inner target. Selections are in `damped_auto_selections.csv`. For Aug 2026 it picked w6_d0.5 (visits), w6_d0.75 (pounds) and w12_d0.5 (individuals).
- **Level-corrected seasonal models:** `snaive_level12` is y_{t-12}·exp(mean of the last 12 log-ratios). `seasonal_index_level` is the last-12-month mean times a multiplicative seasonal index. It fell back to seasonal naive in 2023 and is badly biased because the 2022–23 ramp contaminates the index.
- **Fixed a-priori combinations:** `combo_stat_median` is the median of sf_ets_log, sf_theta_log, ratio_ses and damped_yoy_auto. `combo_ratio_mean` is the mean of ratio_ses, ratio_arima and ratio_theta.

No external data was used, and no parameters were chosen by looking at Protocol A/B scores. The seed is 0. All statsforecast fits are deterministic.

## Key findings
1. **AutoTheta on logs (`sf_theta_log`) has the lowest monthly (Protocol B) MAPE for all three metrics:** visits 4.84%, pounds 4.23%, individuals 5.47%. The `damped_yoy_3m` baseline scores 5.43%, 5.16% and 5.86%, and seasonal naive scores 8.5%, 6.6% and 8.8%. It also leads the 2024–25 August folds for pounds (1.4% vs 2.6% damped / 1.9% seasonal naive).
2. **The advantage over `damped_yoy_3m` is not statistically meaningful.** Paired tests on the 31 monthly APEs give these results for theta vs damped_yoy_3m:
   - visits: −0.59 pp, t-test p=0.61, wins 17/31
   - pounds: −0.93 pp, p=0.33, wins 16/31
   - individuals: −0.39 pp, p=0.73, wins 17/31

   Against seasonal naive, theta improves by −3.7 / −2.4 / −3.3 pp (p=0.04 / 0.08 / 0.10). With about 37 models compared, even those p-values do not survive a multiple-comparison correction.
3. **Theta does worse than `damped_yoy_3m` in the most recent 12 months** (Aug 2025–Jul 2026): visits 6.8% vs 6.0%, pounds 4.2% vs 3.9%, individuals 7.1% vs 6.0%. It is also biased high across all 31 origins, by +1.4% (visits), +1.3% (pounds) and +1.9% (individuals).
4. **The YoY-ratio models were disappointing.** They handle the 2023 ramp very well: Aug 2023 APE is 0.0–4% where seasonal naive misses by 17–26%. But in 2024–25 they over-extrapolate growth (Aug 2024 APE 11–23%), and their monthly MAPE is 6.3–8.8%, worse than `damped_yoy_3m`. Heavier damping (`ratio_mean3_half`) brings them back to roughly the `damped_yoy_3m` level.
5. **The inner-selected `damped_yoy_auto` is worse than the fixed baseline** (monthly 6.6% / 6.0% / 6.5%). Inner 12-month selection is noisy and chases recent regimes.
6. **AutoCES, MSTL, AutoARIMA (on visits and pounds) and seasonal_index_level are clear losers.**

## Nominations
| metric | nominee 1 | nominee 2 |
|---|---|---|
| visits | `sf_theta_log`: monthly 4.84%, Aug 2024–25 3.7%, **Aug 2026 = 243,208** | `damped_yoy_3m` (baseline; none of my other models beat it): **234,496** |
| pounds | `sf_theta_log`: monthly 4.23%, Aug 2024–25 1.4%, **Aug 2026 = 12,723,100** | `sf_ets_log`: monthly 4.77%, Aug 2024–25 1.3%, **12,927,010** |
| individuals | `sf_theta_log`: monthly 5.47%, Aug 2024–25 3.0%, **Aug 2026 = 754,356** | `combo_stat_median`: monthly 5.67%, Aug 2024–25 5.1%, **742,781** |

Why theta: it is the only family that ranks first on Protocol B for all three metrics at once, which makes a pure selection fluke less likely. It also needs no tuning. Even so, the evidence that it beats `damped_yoy_3m` is weak (point 2), and it ran worse over the last year (point 3). I would treat theta as an ensemble member alongside `damped_yoy_3m`, not as a replacement for it.

## Caveats
- The Aug 2023 fold uses the seasonal-naive fallback for every statsforecast model, so their aug_mape is inflated by 2023. Use aug_mape_2024_25 or monthly_mape when comparing them.
- There are only 3 August folds, and Protocol B's 31 origins are serially correlated. Differences under about 1 pp are noise.
- The forecasts for Aug 2026 diverge: visits ranges from about 221k to 278k across models, and the credible models cluster at 231k–244k. Theta's forecasts sit above the damped-YoY forecasts, consistent with its positive bias.
- The w=12 damped variants have NaN for 2023 (an expected failure: not enough history).

## Full results (all models, sorted by monthly MAPE; aug_24_25 = mean of the 2024 and 2025 Aug APEs)

### visits

| model | aug_mape | aug_2023 | aug_2024 | aug_2025 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| sf_theta_log | 8.9% | 19.4% | 1.1% | 6.3% | 3.7% | 4.8% | 243,208 |
| sf_ets_level | 9.8% | 19.4% | 3.0% | 7.1% | 5.1% | 5.4% | 248,820 |
| damped_yoy_3m | 5.3% | 8.6% | 3.7% | 3.6% | 3.6% | 5.4% | 234,496 |
| dyoy_w3_d0.5 | 5.3% | 8.6% | 3.7% | 3.6% | 3.6% | 5.4% | 234,496 |
| combo_stat_median | 7.1% | 11.3% | 4.3% | 5.7% | 5.0% | 5.5% | 242,782 |
| ratio_mean3_half | 5.4% | 9.2% | 3.5% | 3.5% | 3.5% | 5.6% | 234,483 |
| sf_ets_log | 9.2% | 19.4% | 3.0% | 5.2% | 4.1% | 5.6% | 246,839 |
| dyoy_w3_d0.75 | 4.9% | 3.2% | 6.4% | 5.1% | 5.7% | 5.7% | 231,599 |
| dyoy_w6_d0.5 | 7.3% | 10.2% | 8.2% | 3.3% | 5.8% | 5.8% | 242,355 |
| dyoy_w1_d0.5 | 6.7% | 10.3% | 4.0% | 5.8% | 4.9% | 6.0% | 230,651 |
| dyoy_w1_d0.75 | 7.0% | 5.8% | 6.8% | 8.4% | 7.6% | 6.1% | 225,832 |
| dyoy_w6_d0.75 | 7.9% | 5.7% | 13.2% | 4.8% | 9.0% | 6.3% | 243,387 |
| dyoy_w12_d0.5 | 7.1% |  | 11.0% | 3.2% | 7.1% | 6.3% | 243,810 |
| sf_arima_log | 8.9% | 19.4% | 1.5% | 5.8% | 3.7% | 6.4% | 244,709 |
| dyoy_w1_d1.0 | 7.3% | 1.3% | 9.7% | 11.0% | 10.3% | 6.4% | 221,012 |
| damped_yoy_auto | 5.5% | 3.2% | 9.7% | 3.6% | 6.6% | 6.6% | 242,355 |
| dyoy_w3_d0.25 | 5.7% | 14.0% | 1.0% | 2.0% | 1.5% | 6.6% | 237,393 |
| dyoy_w3_d1.0 | 5.9% | 2.1% | 9.1% | 6.6% | 7.9% | 6.6% | 228,703 |
| ratio_theta | 7.2% | 3.4% | 8.9% | 9.1% | 9.0% | 6.7% | 225,327 |
| dyoy_w6_d0.25 | 6.7% | 14.8% | 3.2% | 1.9% | 2.6% | 6.7% | 241,322 |
| dyoy_w12_d0.25 | 3.2% |  | 4.6% | 1.8% | 3.2% | 6.9% | 242,050 |
| dyoy_w1_d0.25 | 6.4% | 14.8% | 1.1% | 3.1% | 2.1% | 7.0% | 235,471 |
| combo_ratio_mean | 8.0% | 1.1% | 14.7% | 8.3% | 11.5% | 7.1% | 229,279 |
| dyoy_w12_d0.75 | 10.9% |  | 17.3% | 4.5% | 10.9% | 7.3% | 245,570 |
| ratio_ets_auto | 6.6% | 0.0% | 11.8% | 7.9% | 9.8% | 7.3% | 231,606 |
| ratio_ses | 6.6% | 0.0% | 11.8% | 7.9% | 9.8% | 7.3% | 231,606 |
| sf_ces_log | 14.8% | 19.4% | 9.8% | 15.3% | 12.6% | 7.3% | 254,741 |
| sf_mstl_log | 15.6% | 19.4% | 13.5% | 13.9% | 13.7% | 7.4% | 255,542 |
| dyoy_w6_d1.0 | 8.5% | 1.1% | 18.2% | 6.2% | 12.2% | 7.4% | 244,420 |
| seasonal_naive | 7.2% | 19.4% | 1.8% | 0.5% | 1.1% | 8.5% | 240,290 |
| ratio_arima | 10.4% | 0.0% | 23.3% | 8.0% | 15.6% | 8.8% | 230,905 |
| dyoy_w12_d1.0 | 14.8% |  | 23.7% | 5.9% | 14.8% | 9.2% | 247,331 |
| snaive_level12 | 10.0% | 0.0% | 24.2% | 5.9% | 15.0% | 9.4% | 246,954 |
| seasonal_index_level | 20.5% | 19.4% | 23.7% | 18.4% | 21.1% | 10.3% | 277,721 |

### pounds

| model | aug_mape | aug_2023 | aug_2024 | aug_2025 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| sf_theta_log | 6.7% | 17.2% | 0.3% | 2.4% | 1.4% | 4.2% | 12,723,103 |
| combo_stat_median | 6.5% | 10.1% | 7.4% | 1.9% | 4.7% | 4.6% | 13,004,149 |
| sf_ets_log | 6.6% | 17.2% | 0.2% | 2.4% | 1.3% | 4.8% | 12,927,009 |
| sf_ets_level | 7.9% | 17.2% | 3.2% | 3.2% | 3.2% | 4.9% | 12,942,816 |
| damped_yoy_3m | 5.1% | 10.1% | 5.1% | 0.0% | 2.6% | 5.2% | 12,850,522 |
| dyoy_w3_d0.5 | 5.1% | 10.1% | 5.1% | 0.0% | 2.6% | 5.2% | 12,850,522 |
| dyoy_w3_d0.75 | 5.3% | 6.5% | 7.9% | 1.6% | 4.8% | 5.2% | 12,864,996 |
| ratio_mean3_half | 5.1% | 10.3% | 4.9% | 0.0% | 2.5% | 5.2% | 12,847,487 |
| dyoy_w6_d0.75 | 5.9% | 6.3% | 11.1% | 0.1% | 5.6% | 5.3% | 13,238,997 |
| dyoy_w6_d0.5 | 6.1% | 10.0% | 7.2% | 1.1% | 4.2% | 5.3% | 13,099,856 |
| dyoy_w3_d0.25 | 5.8% | 13.7% | 2.2% | 1.6% | 1.9% | 5.5% | 12,836,048 |
| dyoy_w3_d1.0 | 5.6% | 2.9% | 10.8% | 3.2% | 7.0% | 5.5% | 12,879,470 |
| dyoy_w6_d0.25 | 6.4% | 13.6% | 3.3% | 2.2% | 2.7% | 5.7% | 12,960,715 |
| dyoy_w6_d1.0 | 6.2% | 2.7% | 15.1% | 0.9% | 8.0% | 5.7% | 13,378,138 |
| dyoy_w1_d0.25 | 6.4% | 13.5% | 3.5% | 2.3% | 2.9% | 5.7% | 12,872,386 |
| dyoy_w1_d0.5 | 6.2% | 9.8% | 7.5% | 1.3% | 4.4% | 5.8% | 12,923,198 |
| dyoy_w12_d0.5 | 5.6% |  | 8.3% | 2.9% | 5.6% | 5.9% | 12,896,076 |
| dyoy_w12_d0.25 | 3.4% |  | 3.8% | 3.0% | 3.4% | 6.0% | 12,858,825 |
| damped_yoy_auto | 6.5% | 2.9% | 15.1% | 1.6% | 8.3% | 6.0% | 13,238,997 |
| dyoy_w1_d0.75 | 6.0% | 6.0% | 11.6% | 0.3% | 6.0% | 6.2% | 12,974,009 |
| ratio_ets_auto | 5.9% | 2.6% | 13.7% | 1.4% | 7.5% | 6.3% | 13,081,289 |
| ratio_ses | 7.1% | 2.6% | 17.2% | 1.4% | 9.3% | 6.3% | 13,081,289 |
| ratio_theta | 7.7% | 4.4% | 15.7% | 3.1% | 9.4% | 6.4% | 12,987,909 |
| dyoy_w12_d0.75 | 7.7% |  | 12.7% | 2.7% | 7.7% | 6.4% | 12,933,327 |
| combo_ratio_mean | 7.5% | 3.2% | 16.7% | 2.5% | 9.6% | 6.4% | 13,050,145 |
| sf_ces_log | 11.0% | 17.2% | 10.6% | 5.1% | 7.8% | 6.5% | 13,489,257 |
| seasonal_naive | 7.0% | 17.2% | 0.6% | 3.2% | 1.9% | 6.6% | 12,821,574 |
| sf_arima_log | 12.0% | 17.2% | 17.2% | 1.4% | 9.3% | 6.6% | 13,142,174 |
| sf_mstl_log | 12.2% | 17.2% | 15.0% | 4.3% | 9.6% | 6.6% | 13,478,634 |
| dyoy_w1_d1.0 | 6.2% | 2.3% | 15.7% | 0.6% | 8.2% | 7.0% | 13,024,821 |
| ratio_arima | 7.6% | 2.6% | 17.2% | 3.1% | 10.2% | 7.1% | 13,081,238 |
| dyoy_w12_d1.0 | 9.8% |  | 17.1% | 2.5% | 9.8% | 7.2% | 12,970,578 |
| snaive_level12 | 7.5% | 2.6% | 17.4% | 2.4% | 9.9% | 7.3% | 12,974,021 |
| seasonal_index_level | 15.2% | 17.2% | 17.1% | 11.3% | 14.2% | 8.1% | 13,946,892 |

### individuals

| model | aug_mape | aug_2023 | aug_2024 | aug_2025 | aug_24_25 | monthly_mape | Aug 2026 fc |
|---|---|---|---|---|---|---|---|
| sf_theta_log | 10.7% | 26.1% | 1.4% | 4.7% | 3.0% | 5.5% | 754,356 |
| combo_stat_median | 8.1% | 14.3% | 6.3% | 3.9% | 5.1% | 5.7% | 742,781 |
| sf_ets_log | 10.0% | 26.1% | 0.7% | 3.1% | 1.9% | 5.8% | 748,181 |
| damped_yoy_3m | 7.5% | 15.0% | 5.3% | 2.1% | 3.7% | 5.9% | 725,230 |
| dyoy_w3_d0.5 | 7.5% | 15.0% | 5.3% | 2.1% | 3.7% | 5.9% | 725,230 |
| dyoy_w6_d0.5 | 8.9% | 14.4% | 9.7% | 2.5% | 6.1% | 5.9% | 746,638 |
| dyoy_w3_d0.75 | 6.8% | 9.5% | 9.1% | 1.9% | 5.5% | 5.9% | 724,209 |
| sf_ets_level | 10.5% | 26.1% | 1.8% | 3.6% | 2.7% | 5.9% | 752,783 |
| ratio_mean3_half | 7.7% | 15.8% | 5.1% | 2.1% | 3.6% | 6.0% | 725,478 |
| damped_yoy_auto | 5.5% | 2.4% | 11.6% | 2.5% | 7.1% | 6.5% | 737,381 |
| dyoy_w6_d0.75 | 8.9% | 8.5% | 15.7% | 2.5% | 9.1% | 6.5% | 756,321 |
| dyoy_w1_d0.75 | 7.8% | 8.3% | 8.1% | 6.8% | 7.5% | 6.6% | 703,141 |
| dyoy_w1_d0.5 | 8.1% | 14.3% | 4.7% | 5.4% | 5.0% | 6.6% | 711,184 |
| ratio_ets_auto | 6.5% | 2.4% | 11.2% | 5.9% | 8.5% | 6.7% | 717,935 |
| dyoy_w6_d0.25 | 8.8% | 20.3% | 3.7% | 2.5% | 3.1% | 6.9% | 736,955 |
| dyoy_w12_d0.5 | 8.6% |  | 13.4% | 3.8% | 8.6% | 6.9% | 737,381 |
| dyoy_w3_d1.0 | 6.2% | 3.9% | 12.9% | 1.7% | 7.3% | 7.0% | 723,188 |
| dyoy_w3_d0.25 | 8.2% | 20.6% | 1.5% | 2.4% | 1.9% | 7.0% | 726,251 |
| dyoy_w12_d0.25 | 4.4% |  | 5.6% | 3.2% | 4.4% | 7.0% | 732,326 |
| ratio_theta | 6.0% | 4.4% | 10.4% | 3.3% | 6.8% | 7.0% | 711,544 |
| dyoy_w1_d1.0 | 7.4% | 2.4% | 11.6% | 8.3% | 9.9% | 7.1% | 695,097 |
| sf_arima_log | 9.9% | 26.1% | 1.4% | 2.2% | 1.8% | 7.2% | 729,174 |
| dyoy_w1_d0.25 | 8.5% | 20.2% | 1.2% | 4.0% | 2.6% | 7.3% | 719,228 |
| sf_ces_log | 16.2% | 26.1% | 9.3% | 13.1% | 11.2% | 7.3% | 778,012 |
| ratio_ses | 6.5% | 2.4% | 11.2% | 5.9% | 8.5% | 7.4% | 717,935 |
| combo_ratio_mean | 7.1% | 2.7% | 12.8% | 5.8% | 9.3% | 7.5% | 715,760 |
| sf_mstl_log | 16.3% | 26.1% | 12.7% | 10.2% | 11.4% | 7.5% | 770,799 |
| dyoy_w6_d1.0 | 8.9% | 2.7% | 21.6% | 2.5% | 12.1% | 8.1% | 766,004 |
| ratio_arima | 8.8% | 1.3% | 16.7% | 8.3% | 12.5% | 8.2% | 717,802 |
| dyoy_w12_d0.75 | 12.8% |  | 21.2% | 4.5% | 12.8% | 8.2% | 742,435 |
| seasonal_naive | 10.3% | 26.1% | 2.3% | 2.6% | 2.4% | 8.8% | 727,272 |
| dyoy_w12_d1.0 | 17.1% |  | 29.0% | 5.1% | 17.1% | 10.5% | 747,490 |
| snaive_level12 | 12.0% | 1.3% | 29.7% | 5.1% | 17.4% | 10.7% | 746,261 |
| seasonal_index_level | 25.2% | 26.1% | 29.0% | 20.4% | 24.7% | 12.9% | 848,991 |
