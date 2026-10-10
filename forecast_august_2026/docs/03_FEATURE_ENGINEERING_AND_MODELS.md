# Feature Engineering and Models

## County-panel design

The primary machine-learning design was a global county panel. Instead of
fitting one model per county, all eligible county-month rows were stacked into a
single training table. Separate models were fitted for visits, pounds, and
individuals.

Benefits of this structure included:

- Small counties could borrow information from larger counties.
- County identity still captured persistent county differences.
- The model had thousands of county-month rows instead of only 55 statewide
  rows.
- A single feature and validation policy could be applied consistently.

The additional panel rows do not create additional years of statewide history.
There are still only about four annual cycles, which limits trend and seasonal
inference.

## Engineered feature groups

### Outcome history

For each target:

- Lags 1, 2, 3, 6, 12, and 13 months
- Rolling means over 3, 6, and 12 months
- Rolling medians over 3, 6, and 12 months
- Year-over-year growth
- Year-to-date total through the preceding month
- Year-to-date growth relative to the comparable prior-year period
- Prior-years-only historical month-to-previous-month ratio
- Prior-month county share of the statewide outcome

All rolling and lagged values were computed from the previous month or earlier.

### Cross-metric predictors

Each target model could use prior values of the other outcomes:

- Lagged visits
- Lagged pounds
- Lagged individuals
- Lagged pounds per visit
- Lagged individuals per visit

For example, the pounds model could use past visits and past pounds per visit,
while never seeing the current August values.

### Reporting coverage

Only lagged coverage was used:

- Prior-month number of sites
- Prior-month number of reporting sites
- Prior-month number of missing sites
- Twelve-month coverage lags
- Prior-month reporting rate

Same-month August coverage was prohibited because it would not be known at the
July 31 forecast cutoff.

### Time and seasonality

- Linear month index
- Calendar-month category
- Month sine
- Month cosine

The categorical month representation supported discrete seasonal effects, while
sine and cosine encoded the cyclical relationship between December and January.

### SNAP sensitivity features

- Latest available SNAP cases
- Latest available SNAP people
- Latest available SNAP expenditure
- People per SNAP case
- Year-over-year changes
- Months since the latest SNAP observation

These variables were used only in the SNAP sensitivity model.

## Baseline models

### Seasonal naive

The August forecast equals the previous August outcome.

This is the principal benchmark because it is simple, transparent, seasonal,
and difficult to beat consistently in a short monthly series.

### Year-to-date growth

The previous August value is multiplied by January–July growth from the prior
year to the current year.

### Historical August/July ratio

Current July is multiplied by the median historical August-to-July ratio
available before the cutoff.

### Trend plus monthly regression

An ordinary least-squares regression includes:

- Intercept
- Linear time trend
- Calendar-month indicators

### Robust baseline ensemble

The median of seasonal naive, year-to-date growth, August/July ratio, and
trend-month regression.

## Statistical time-series models

### ETS / Holt-Winters

Candidate specifications included:

- Damped additive trend
- Level-only exponential smoothing
- Additive damped trend with additive 12-month seasonality when at least 24
  months were available
- Additive 12-month seasonality without trend

The candidate with the lowest training AIC within the cutoff was used.

### Constrained SARIMA

A deliberately small candidate set was tested:

- SARIMA(0,1,1)(0,1,1,12)
- SARIMA(1,0,0)(1,0,0,12)
- SARIMA(1,1,0)(0,1,1,12)

The AIC-selected configuration was fitted within each cutoff. A large parameter
search was intentionally avoided because only 55 months were available.

## Regularized county-panel models

### Ridge

Ridge applies L2 regularization. It shrinks correlated predictors together and
was expected to be stable when lag and rolling variables contained overlapping
information.

Candidate `alpha` values were 0.1, 1, 10, and 100.

### LASSO

LASSO applies L1 regularization and can set coefficients to zero. It was tested
as a predictive model and an exploratory feature-selection method.

Candidate `alpha` values were 0.001, 0.005, 0.01, and 0.05.

LASSO zeros should not be interpreted as permanent proof that a feature is
irrelevant. With correlated variables and short history, the selected member of
a correlated feature group can change across folds.

### Elastic Net

Elastic Net combines L1 and L2 penalties. It was expected to retain correlated
feature groups more reliably than pure LASSO while still allowing some sparsity.

The tuning grid combined:

- `alpha`: 0.001, 0.01, and 0.05
- `l1_ratio`: 0.2, 0.5, and 0.8

All regularization settings were selected through inner chronological
validation within each outer training period.

## Tree-based model

### Global county-panel LightGBM

LightGBM used conservative settings:

- 250 trees
- Learning rate 0.025
- Maximum depth 4
- 15 leaves
- Minimum 60 observations per leaf
- Row and feature subsampling
- L1 and L2 regularization
- Fixed random seed 2026
- Absolute-error objective

One version used only eligible food-shelf features. A second version added SNAP
features and was explicitly marked sensitivity-only.

## Structural models

Pounds and individuals were also forecast using a decomposed relationship:

- Forecast pounds = forecast visits × forecast pounds per visit
- Forecast individuals = forecast visits × forecast individuals per visit

The visit component came from the Elastic Net county-panel model. The per-visit
ratio used historical August ratios by county, with recent and statewide
fallbacks where necessary.

These models tested whether demand volume and service intensity were easier to
forecast separately than the total outcome directly.

## Ensemble models

### Robust baseline ensemble

This was the median of the four original baseline forecasts.

### Core median ensemble

This was defined before examining the final August 2026 outcome as the median
of:

- Seasonal naive
- ETS
- Elastic Net county panel
- LightGBM county panel

The same four components were used in every backtest and for the final forecast.

## Models not fitted

Deep learning, including N-BEATS, LSTM, and Transformers, was not fitted. The
statewide history contains only 55 months, or roughly four annual cycles.
Although a pooled neural model could technically be trained on county rows, the
underlying time diversity is still too limited for a credible primary model or
meaningful hyperparameter comparison.

CatBoost was not required because LightGBM already provided the intended
nonlinear tree-based challenger. Random Forest was also omitted because it is
poor at trend extrapolation and would add another correlated tree benchmark
without resolving the short-history limitation.

## Class-notebook usage

The supplied course notebooks were used only as references for:

- Scikit-learn preprocessing pipelines
- Standardization
- Ridge, LASSO, and Elastic Net concepts
- Feature comparison
- The warning that feature selection must be nested inside validation

Their random train/test and random K-fold examples were not copied because
random splitting is inappropriate for forecasting. Chronological rolling-origin
validation replaced random cross-validation.

