# Executive Summary

## Objective

The objective was to forecast three statewide Minnesota food-shelf outcomes for
August 2026:

- Visits
- Pounds distributed
- Individuals served

The final information cutoff was July 31, 2026. August 2026 outcomes, partial
reporting information, same-month coverage, and other post-cutoff information
were prohibited.

## What was completed

The work expanded the original baseline pipeline into a full comparison of:

- Required forecasting baselines
- ETS and SARIMA time-series models
- Global county-panel Ridge, LASSO, and Elastic Net models
- Global county-panel LightGBM
- A SNAP-enhanced LightGBM sensitivity model
- Structural visits-times-ratio models
- Two ensemble approaches

The advanced pipeline pooled 86 eligible counties rather than building 86
independent models. This allowed counties to share information while retaining
county identity, their own lag history, coverage, and seasonal patterns. Wilkin
County was excluded from county modeling because the supplied data contain no
food-shelf site there; it was not replaced with a false zero.

Feature engineering included prior-only lags, rolling statistics, year-over-year
growth, year-to-date growth, historical month ratios, county share, calendar
seasonality, lagged site coverage, cross-metric history, and per-visit ratios.

Every transformation that learns from data—including imputation, scaling, and
regularization tuning—was repeated inside the applicable historical training
cutoff.

## Validation design

Three historical August forecasts were used as outer tests:

| Training information | Held-out prediction |
|---|---|
| Through July 31, 2023 | August 2023 |
| Through July 31, 2024 | August 2024 |
| Through July 31, 2025 | August 2025 |

The primary metric was provisional MAPE. Supporting metrics were median APE,
MAE, RMSE, WAPE, county-level WAPE, county-level sMAPE, and the number of August
folds in which a challenger beat seasonal naive.

## Main results

The model with the lowest average MAPE was different for each outcome:

| Target | Lowest-average-MAPE model | Mean MAPE | Folds beating seasonal naive |
|---|---|---:|---:|
| Visits | LASSO county panel | **4.37%** | 2/3 |
| Pounds | Ridge county panel | **1.94%** | 2/3 |
| Individuals | ETS | **4.69%** | 2/3 |

These averages are promising, but none of those three models beat seasonal
naive in every historical August. Their strong averages were not considered
sufficient evidence of stable superiority with only three outer folds.

The core median ensemble was the only challenger that beat seasonal naive in
all three individual-service folds. Its mean MAPE was 6.54%, compared with
10.49% for seasonal naive.

## Selected models and forecasts

The conservative selection rule required a challenger to:

1. Have lower mean MAPE than seasonal naive.
2. Beat seasonal naive in every August fold.
3. Be eligible under the cutoff and feature-availability policy.

| Target | Selected model | Mean MAPE | August 2026 forecast |
|---|---|---:|---:|
| Visits | Seasonal naive | 7.20% | **240,280** |
| Pounds | Seasonal naive | 7.03% | **12,821,474.42** |
| Individuals | Core median ensemble | 6.54% | **721,409.79** |

The individuals ensemble is the median of four independently generated
forecasts:

- Seasonal naive
- ETS
- Elastic Net county panel
- LightGBM county panel

## Key insights

- There was no universally best model. Different outcomes favored different
  model families.
- Regularization helped. LASSO was strongest on average for visits, and Ridge
  was strongest on average for pounds.
- Simpler methods remained difficult to beat consistently. Seasonal naive was
  retained for visits and pounds because advanced challengers lost in one of
  the three historical Augusts.
- The ensemble provided a stable improvement for individuals, winning all
  three August comparisons.
- LightGBM performed poorly, with approximately 21% MAPE for all three targets.
  The nonlinear model was too complex relative to the short time history.
- SNAP features did not improve LightGBM. SNAP remained sensitivity-only because
  its exact historical publication dates were not verified.
- Deep learning was not fitted. The dataset contains only 55 statewide months,
  or approximately four annual cycles, which is insufficient evidence for a
  credible primary neural forecast.
- More historical monthly data would likely be more valuable than adding model
  complexity.

## Important target-scope warning

The advanced experiment uses the newer clean forecasting export, which excludes
2,702 meal-program rows. The earlier isolated baseline source includes those
rows. Consequently, the two pipelines have slightly different visits and pounds
totals and materially different individual totals.

Results from those target definitions must not be mixed in one leaderboard.
The competition's intended scope must be confirmed before the final submission.

