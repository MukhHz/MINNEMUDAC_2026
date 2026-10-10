# Validation, Results, and Model Selection

## Outer rolling-origin backtests

The model evaluation simulated the real August 2026 task three times:

```text
Train through July 2023 -> predict August 2023 -> score
Train through July 2024 -> predict August 2024 -> score
Train through July 2025 -> predict August 2025 -> score
```

Each held-out August was retrieved only after the models generated their
predictions.

## Inner tuning

Ridge, LASSO, and Elastic Net hyperparameters were selected inside each outer
training period. The last four eligible historical months were used as
time-ordered validation dates where sufficient earlier training history was
available.

For every validation date:

- Training rows occurred strictly before validation.
- The imputer and scaler were refitted on the inner training data.
- Hyperparameters were evaluated using county-level WAPE on the next month.

The held-out August used for outer scoring never participated in tuning.

## Evaluation metrics

### MAPE

Mean absolute percentage error was the provisional primary statewide metric:

```text
MAPE = mean(abs(actual - forecast) / actual)
```

Statewide totals are far from zero, so MAPE is interpretable for the primary
comparison.

### Supporting statewide metrics

- Median absolute percentage error
- Mean absolute error
- Root mean squared error
- Weighted absolute percentage error
- Number of folds beating seasonal naive

### County metrics

- WAPE
- MAE
- RMSE
- sMAPE
- Median APE

County MAPE was not emphasized because zero or very small county outcomes can
produce misleading percentage errors.

## Meaning of 2/3 and 3/3

There were three independent historical August tests. A model with a 2/3 result
had a lower absolute percentage error than seasonal naive in two years but a
higher error in the third year.

A 3/3 result means the challenger beat seasonal naive in August 2023, August
2024, and August 2025.

The fold count matters because a model can have an excellent average MAPE due to
one exceptional year while still being less reliable in another year.

## Mean August MAPE by model

Lower values are better.

| Model | Visits | Pounds | Individuals |
|---|---:|---:|---:|
| Seasonal naive | 7.20% | 7.03% | 10.49% |
| YTD growth | 8.99% | 6.70% | 9.69% |
| August/July ratio | 10.15% | 9.62% | 10.08% |
| Trend plus monthly regression | 13.05% | 10.20% | 15.47% |
| Robust baseline ensemble | 9.15% | 8.10% | 9.40% |
| ETS | 6.84% | 5.89% | **4.69%** |
| SARIMA | 6.88% | 8.69% | 8.39% |
| Ridge county panel | 9.36% | **1.94%** | 13.61% |
| LASSO county panel | **4.37%** | 9.35% | 6.28% |
| Elastic Net county panel | 5.52% | 9.05% | 6.95% |
| LightGBM county panel | 21.39% | 21.58% | 21.42% |
| LightGBM plus SNAP sensitivity | 20.81% | 21.78% | 21.65% |
| Structural visits × ratio | Not applicable | 2.75% | 7.21% |
| Core median ensemble | 6.80% | 5.84% | 6.54% |

## Lowest-average models

| Target | Lowest-average model | Mean MAPE | Fold wins vs. naive |
|---|---|---:|---:|
| Visits | LASSO county panel | 4.37% | 2/3 |
| Pounds | Ridge county panel | 1.94% | 2/3 |
| Individuals | ETS | 4.69% | 2/3 |

These are the strongest models by average MAPE, but they were not automatically
selected because each lost to seasonal naive in one of the three Augusts.

## Conservative selection rule

For each target, a challenger was selected only when it:

1. Had lower mean MAPE than seasonal naive.
2. Beat seasonal naive in all three August folds.
3. Was eligible under the cutoff policy.

If no challenger satisfied every requirement, seasonal naive remained selected.

## Selection outcome

### Visits

LASSO achieved the best mean MAPE at 4.37%, compared with 7.20% for seasonal
naive, but it won only 2/3 folds. Seasonal naive remained the selected model.

### Pounds

Ridge achieved the best mean MAPE at 1.94%, compared with 7.03% for seasonal
naive, but it won only 2/3 folds. The structural model was also promising at
2.75% MAPE and 2/3 wins. Seasonal naive remained selected.

### Individuals

ETS achieved the best average MAPE at 4.69% but won only 2/3 folds. The core
median ensemble had 6.54% MAPE and beat seasonal naive in all 3/3 folds. The
ensemble was therefore selected.

## Final August 2026 forecasts

| Target | Selected model | Forecast |
|---|---|---:|
| Visits | Seasonal naive | **240,280** |
| Pounds distributed | Seasonal naive | **12,821,474.42** |
| Individuals served | Core median ensemble | **721,409.79** |

## Interpretation of forecast quality

The selected statewide MAPEs are all below 10%, which is generally a good level
of forecast accuracy:

- Visits: 7.20%
- Pounds: 7.03%
- Individuals: 6.54%

The lower average errors from LASSO, Ridge, and ETS are excellent directional
signals, but the evidence is based on only three historical Augusts. The current
model choice emphasizes stability rather than choosing a model because of one
exceptionally strong year.

## Model-family conclusions

- **Baselines:** Strong and difficult to beat consistently.
- **Statistical time series:** ETS was especially strong for individuals.
- **Regularized regression:** Strongest advanced family overall; LASSO helped
  visits, Ridge helped pounds, and Elastic Net was competitive for individuals.
- **Tree-based ML:** LightGBM was not competitive and systematically
  underforecasted several folds.
- **SNAP:** No demonstrated incremental improvement in the tested LightGBM
  specification.
- **Structural models:** Promising for pounds but not stable enough for primary
  selection.
- **Ensembles:** The core ensemble was successful for individuals but not stable
  enough to replace seasonal naive for visits or pounds.
- **Deep learning:** Not evaluated; no claim of good or bad deep-learning
  performance can be made from this experiment.

## Limitations

- Only three August holdouts exist.
- There are only 55 statewide months.
- The official scoring metric was not yet confirmed, so MAPE is provisional.
- County-panel rows increase cross-sectional sample size but do not create more
  annual cycles.
- External-variable publication dates remain imperfectly verified.
- The target-scope discrepancy concerning meal-program rows must be resolved.
- Model rankings may change if additional historical months or the official
  scoring rule become available.

