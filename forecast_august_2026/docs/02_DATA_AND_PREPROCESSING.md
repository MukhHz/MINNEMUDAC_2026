# Data and Preprocessing

## Input datasets

The advanced pipeline used three clean exports:

| File | Purpose |
|---|---|
| `forecasting_pipeline/data/food_county_month_clean.csv` | County-month food-shelf outcomes, site coverage, imputations, and diagnostic fields |
| `forecasting_pipeline/data/food_statewide_month_clean.csv` | Statewide monthly reported and imputed outcomes |
| `forecasting_pipeline/data/snap_state_month_clean.csv` | Statewide SNAP cases, people, expenditure, and assumed availability dates |

The county dataset contained 4,785 county-month rows: 87 counties across 55
months from January 2022 through July 2026. The statewide dataset contained 55
monthly observations.

Only 86 counties were eligible for county-panel forecasting. Wilkin County had
no supplied food-shelf site and remained structural missing rather than being
treated as zero.

## Forecast targets

The primary target version was the reported series:

- `visits_reported`
- `pounds_reported`
- `individuals_reported`

The imputed target series were not used as primary outcomes. Prior masked-value
validation showed high imputation error, so imputed outcomes remain suitable
only for sensitivity analysis.

All three predictions were statewide August totals.

## Data-scope reconciliation

Two prepared sources exist in the project:

1. `Data/processed/foodshelf_site_month.csv`, used by the earlier isolated
   baseline pipeline.
2. `forecasting_pipeline/data/food_site_month_clean.csv`, used by the advanced
   pipeline.

The earlier source contains 28,101 site-month rows and includes 2,702
meal-program rows. The advanced clean export contains 25,399 site-month rows and
excludes those meal-program observations.

This difference explains why the advanced August 2025 values—and therefore the
August 2026 seasonal-naive forecasts—do not exactly match the original isolated
baseline results. The discrepancy is recorded in
`advanced_results/source_scope_audit.csv`.

The advanced comparison is internally consistent: every model and baseline in
its leaderboard uses the same non-meal target definition.

## Existing cleaning retained

The modeling pipeline began from the cleaned exports and did not redo the
original data-cleaning notebook. The existing preparation had already:

- Resolved documented blank and exact duplicates.
- Summed legitimate duplicate streams.
- Corrected documented impossible or clear typo values.
- Standardized dates, counties, and FIPS identifiers.
- Constructed a complete county-month grid.
- Marked structural missingness.
- Created outlier and data-quality diagnostic fields.

No observations were removed, clipped, or winsorized merely because they made
forecast performance worse.

## Missing-value handling

For regularized regression, numeric feature missingness was filled with the
training-fold median. The imputer was fitted separately inside each training
fold. Validation and target rows never contributed to the imputation values.

LightGBM was placed behind the same explicit feature preprocessing so all model
inputs were reproducible and consistently encoded.

Early rows naturally lack 6- or 12-month lags. These features were retained and
handled by fold-local imputation rather than deleting most of the already short
history.

## Standardization

Standardization was applied to numeric predictors for:

- Ridge
- LASSO
- Elastic Net

The standard scaler was fitted only on each training fold. This is essential
because fitting it once on the complete dataset would allow future feature
distributions to influence earlier backtests.

Standardization was not required for the baseline formulas, ETS, SARIMA, or
LightGBM.

## Target transformation

County-panel machine-learning targets were modeled as `log1p(outcome)`. Model
outputs were converted back using `expm1` and clipped at zero. This approach:

- Prevented negative forecasts.
- Reduced the influence of very large counties.
- Made the scale difference among counties easier for regularized models to
  handle.

Statewide statistical models operated on the original outcome scale.

## Categorical encoding

Two categorical variables were used:

- County FIPS
- Calendar month

They were one-hot encoded with unknown-category handling. County identity let a
single global model learn county-specific offsets without fitting 86 separate
models.

## Point-in-time cutoff rules

The final forecast used only information available by July 31, 2026. Historical
folds used equivalent simulated cutoffs.

The following rules were enforced:

- The held-out August target was absent from training.
- Outcome lags and rolling features used `shift(1)` or older information.
- Same-month target values were prohibited.
- Same-month reporting-site counts and outlier flags were prohibited.
- Current-month partial reporting was prohibited.
- Historical feature engineering, imputation, scaling, tuning, and fitting were
  repeated inside each cutoff.
- Predictions were generated before the held-out August actual was retrieved for
  scoring.

## External variables

SNAP data were joined using a conservative assumed three-month release lag. The
latest SNAP record whose assumed availability date was on or before the cutoff
was used. Because exact publication dates were not verified, SNAP features were
restricted to a separately labeled sensitivity model and could not be selected
as the primary forecast.

Poverty and Map the Meal Gap variables were excluded from the primary modeling
experiment. Under the conservative availability policy, they do not provide a
consistent point-in-time feature history for all three August backtests,
especially the August 2023 fold.

