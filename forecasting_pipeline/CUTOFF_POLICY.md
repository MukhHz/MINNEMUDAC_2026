# Point-in-time cutoff policy

## Final forecast

The final August 2026 forecast may use only information available on or before
July 31, 2026. No August 2026 outcome, partial outcome, reporting-site count,
outlier flag, or external feature may be used.

## Historical backtests

Use these simulated information cutoffs:

| Forecast target | Maximum information date |
|---|---|
| August 2023 | July 31, 2023 |
| August 2024 | July 31, 2024 |
| August 2025 | July 31, 2025 |
| August 2026 | July 31, 2026 |

Imputation, outlier detection, feature engineering, scaling, feature selection,
and model fitting must be repeated inside each cutoff. Do not clean the full
series once and then slice it for a historical backtest.

## Source-specific rules

- Food-shelf outcomes: a month is treated as available at that month's end.
- SNAP: the notebook currently applies a conservative three-month release lag.
  Exact publication dates are not yet verified.
- ACS poverty: the notebook conservatively treats a year as available on
  December 31 of the following year. Exact release dates are not yet verified.
- MMG: the release year is parsed from the supplied source filename and treated
  as available on December 31 of that year. Exact release dates are not yet
  verified.
- SNAP agency codes are not county FIPS. Use statewide SNAP totals unless an
  approved agency-to-county allocation is provided.
- Wilkin County has no food-shelf site in the supplied data. Its outcomes remain
  structural missing and must not be replaced with zero.

External features with unverified availability dates may be used only in
sensitivity experiments, not in the final submitted model.

## Leakage rules

- Same-month target values and same-month outcome-derived outlier flags are
  prohibited predictors.
- Lagged outcomes, lagged outlier flags, and rolling statistics must use
  shift(1) or an equivalent prior-period operation.
- A held-out August outcome must never be imputed.
- Every feature row must pass assert_information_cutoff from cutoff_checks.py.

