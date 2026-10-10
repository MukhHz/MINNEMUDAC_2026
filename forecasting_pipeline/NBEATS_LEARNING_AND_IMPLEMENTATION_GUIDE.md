# N-BEATS learning and implementation guide

## Purpose

This is the first model-learning guide for the August 2026 forecasting project. It explains N-BEATS from first principles, connects it to the prepared Minnesota food-shelf data, and defines the implementation and evaluation plan we will follow in the next step.

The goal is not to use deep learning because it sounds advanced. The goal is to test whether a small, global N-BEATS model produces repeatable out-of-sample improvement over the current seasonal-naive baseline.

## 1. The forecasting problem in this project

We want to predict August outcomes using only information available through July 31 of the same year.

Primary targets:

1. Visits
2. Pounds distributed
3. Individuals served

Later extensions can model adults, children, and seniors.

The two prepared data views have different purposes:

| Data | Shape | Appropriate use |
|---|---:|---|
| `forecast_august_2026/results/monthly_series.csv` | 55 statewide months | Simple learning prototype and comparison with the existing statewide baseline |
| `forecasting_pipeline/data/food_county_month_clean.csv` | 4,785 rows = 87 counties x 55 months | Global county-panel N-BEATS experiment |

The county grid runs from January 2022 through July 2026. Wilkin County has no food-shelf site in the supplied data, so its 55 rows are structurally missing. It must not be converted to zero. The global model should use the 86 counties with sites and preserve Wilkin as structural missing.

The primary benchmark remains the reported statewide outcome. The existing imputed county outcomes are a sensitivity series, not automatically the primary target. Any imputation used in a historical fold must be re-created using only information available at that fold's cutoff.

## 2. What N-BEATS is

N-BEATS means **Neural Basis Expansion Analysis for Time Series Forecasting**. It is a feed-forward neural network designed specifically for forecasting a univariate time series.

For one training example, the model receives a fixed history window:

```text
input = [y(t-L+1), ..., y(t-1), y(t)]
```

It produces the next `H` values:

```text
forecast = [y(t+1), ..., y(t+H)]
```

For this project:

```text
L = 12 historical months
H = 1 future month
```

An N-BEATS block produces two outputs:

- **Backcast:** the portion of the input window that the block explains.
- **Forecast:** that block's contribution to the future prediction.

After each block, the explained backcast is removed from the remaining input:

```text
remaining input after block k
    = remaining input before block k - block k backcast
```

The final forecast is the sum of all block forecasts:

```text
final forecast = forecast block 1 + forecast block 2 + ... + forecast block K
```

This pair of residual paths is the key idea:

- the backward residual tells later blocks what history is still unexplained;
- the forward residual adds each block's forecast contribution.

N-BEATS is not an LSTM and has no recurrent hidden state. Its blocks are multilayer perceptrons operating on fixed windows.

## 3. Generic versus interpretable N-BEATS

There are two main configurations.

### Generic N-BEATS

Generic blocks learn flexible basis coefficients without forcing the forecast to look like a particular trend or seasonal curve. This is the correct first implementation for this project.

### Interpretable N-BEATS

Interpretable stacks project their outputs onto predefined bases:

- polynomial-like bases for trend;
- harmonic bases for seasonality.

This makes trend and seasonal contributions easier to inspect, but it is not the right first configuration here. The current Nixtla `NBEATS` implementation rejects trend or seasonality stacks when `h=1`, because those bases collapse at a one-step horizon. Our first model will therefore use only an identity stack. A later learning exercise can use a longer horizon to study decomposition, but it should not replace the one-month competition experiment without a fair backtest.

## 4. What “global” means

A local model learns from one time series. A global model uses one shared set of neural-network weights across many related series.

For visits, the long-format training table will conceptually be:

| `unique_id` | `ds` | `y` |
|---|---|---:|
| Aitkin | 2022-01-01 | visits for Aitkin |
| Aitkin | 2022-02-01 | visits for Aitkin |
| ... | ... | ... |
| Wright | 2026-07-01 | visits for Wright |

The model slides a 12-month window over every eligible county. It learns one forecasting function from all windows rather than fitting 86 separate networks.

We will still fit one global model per outcome:

```text
global visits N-BEATS
global pounds N-BEATS
global individuals N-BEATS
```

Do not combine the three targets into one `y` column. Standard N-BEATS is univariate: each training row has one target, even though the weights are shared across counties.

## 5. Why N-BEATS is an experiment, not the expected winner

The county panel gives more training windows than the 55-row statewide series, but it still contains only about four and a half annual cycles. Neural networks can fit noise when history is short.

N-BEATS earns a place in the comparison because it:

- pools information across counties;
- learns nonlinear relationships among recent lags;
- directly optimizes forecast error;
- provides a useful deep-learning benchmark.

It remains experimental because:

- the time span is short;
- county scales vary greatly;
- a few county-month targets are missing;
- only three historical August folds are available;
- the existing seasonal-naive model is already strong.

A more complex model is accepted only if it improves genuine future forecasts, not because its training loss is lower.

## 6. Concepts to learn before coding

Learn these in order.

### 6.1 Time ordering

A forecast can use only the past. Random train/test splitting is invalid because it allows later months to teach a model that is evaluated on earlier months.

### 6.2 Sliding windows

With `input_size=12` and `h=1`, a window uses 12 months to predict the thirteenth:

```text
Jan 2022 ... Dec 2022 -> Jan 2023
Feb 2022 ... Jan 2023 -> Feb 2023
```

### 6.3 Scaling

Hennepin County and a small county can differ by orders of magnitude. Scaling prevents large series from dominating gradient updates solely because of their size. We will begin with robust per-series scaling and verify that predictions are returned to the original units.

### 6.4 Loss function

The training loss tells the optimizer which errors to reduce. We will start with MAE because it is less dominated by very large errors than MSE and remains defined near zero. MAPE is not the training loss because it becomes unstable for small denominators.

### 6.5 Gradient descent

The model makes a prediction, measures loss, calculates how each weight contributed to the error, and updates the weights. One update is a training step. The learning rate controls the update size.

### 6.6 Regularization and early stopping

A small network, shared block weights, a limited training budget, and early stopping reduce the chance of memorizing the short history.

### 6.7 Validation versus test

- **Training data** updates weights.
- **Inner validation data** selects training duration or hyperparameters.
- **Outer held-out August** estimates final performance and must never guide that fold's model.

## 7. Parameters we will use first

This is the starting configuration, not a claim that these values are optimal.

| Parameter | First value | Meaning and reason |
|---|---:|---|
| `h` | `1` | Predict August from data through July. |
| `input_size` | `12` | One annual cycle. The July 2023 cutoff has only 19 months, so a 24-month window is not consistently available. |
| `stack_types` | `['identity']` | Generic N-BEATS; compatible with a one-month horizon in the current library. |
| `n_blocks` | `[2]` | Small network for limited data. |
| `mlp_units` | `[[64, 64]]` | Two modest hidden layers rather than the much larger defaults. |
| `shared_weights` | `True` | Reduces the number of free parameters. |
| `activation` | `'ReLU'` | Standard nonlinear activation and a sensible default. |
| `loss` | `MAE()` | Robust starting objective in original target units after scaling. |
| `valid_loss` | `MAE()` | Early stopping should monitor the same clear objective initially. |
| `scaler_type` | `'robust'` | Helps with very different county scales and large values. |
| `learning_rate` | `1e-3` | Conservative Adam starting rate. |
| `max_steps` | `500` | Upper limit; early stopping should usually stop sooner. |
| `val_check_steps` | `25` | Check validation often enough for a small dataset. |
| `early_stop_patience_steps` | `5` | Stop after repeated validation checks without improvement. |
| `batch_size` | `32` | Number of series sampled per batch. |
| `windows_batch_size` | `256` | Modest number of sliding windows per optimization batch. |
| `random_seed` | `1`, then `7`, `42` | Measure seed sensitivity instead of trusting one lucky run. |

Only a small, predeclared set should be tuned:

```text
input_size:       12 or 18
hidden width:     32 or 64
n_blocks:         1 or 2
learning_rate:    0.001 or 0.0003
```

The 24-month window is excluded from the locked three-fold comparison because it is unavailable at the July 2023 cutoff without padding. Start-padding would change the experiment and should be reported separately.

## 8. Data decisions that must be explicit

### 8.1 Reported versus imputed outcomes

Use two clearly labeled experiments:

1. **Primary reported experiment:** preserve reported outcomes and an availability mask. Training windows with unavailable inputs or labels must be excluded or masked; a held-out August is never imputed.
2. **Imputed sensitivity experiment:** use imputed values only when the imputation was produced inside the historical cutoff. Score and report it separately.

Do not silently fill missing targets with zero, forward-fill them, or use a full-history imputation before slicing historical folds.

### 8.2 Wilkin County

Exclude Wilkin from model fitting because it has no site and all 55 outcomes are structurally missing. Keep an audit record showing that it was excluded for this reason. Do not represent it as a zero-demand county.

### 8.3 Nonnegative predictions

Food-shelf outcomes cannot be negative. Retain all observed values unchanged, but transform final model predictions with:

```python
prediction = max(0.0, prediction)
```

Report whether clipping occurred and how often. Frequent clipping is a model warning.

### 8.4 County forecasts and statewide totals

For each fold, produce all county forecasts first. Then sum them to obtain the statewide forecast. Preserve both levels in the results so that a good statewide total cannot hide large offsetting county errors.

## 9. Leakage-safe backtest

Run the same outer folds used by the baseline:

| Fold | Maximum training information | Held-out target |
|---|---|---|
| 1 | July 31, 2023 | August 2023 |
| 2 | July 31, 2024 | August 2024 |
| 3 | July 31, 2025 | August 2025 |

For each target and outer fold:

1. Slice all raw inputs at the fold cutoff.
2. Re-create any imputation or scaling using only that slice.
3. Build 12-month input windows whose label occurs no later than the cutoff.
4. Reserve recent pre-cutoff windows for inner validation.
5. Select hyperparameters without looking at the held-out August.
6. Refit the chosen configuration within the fold.
7. Predict each eligible county's held-out August.
8. Apply the nonnegative prediction rule.
9. Retrieve the August actuals only after predictions are fixed.
10. Score county forecasts and their statewide sum.

For the final run, train through July 31, 2026 and predict August 2026. No August 2026 value, partial report, missing-site count, or flag may enter the model.

## 10. Evaluation: how to know whether it works

There are four separate questions.

### 10.1 Did the code run correctly?

Minimum checks:

- every series is ordered by date;
- each county has at most one row per month;
- every input month precedes its label month;
- no fold contains data after its cutoff;
- prediction rows match the intended county and August;
- units are restored after scaling;
- Wilkin remains structural missing;
- forecasts are generated before held-out actuals are joined.

### 10.2 Did training behave sensibly?

Good signs:

- training loss decreases;
- validation loss improves and then levels off;
- early stopping occurs before extreme over-training;
- predictions vary across counties and are not all constant;
- only rare or no forecasts require clipping.

Warning signs:

- training loss falls while validation loss rises;
- loss becomes `NaN` or explodes;
- every county receives nearly the same scaled prediction;
- predictions change drastically with a different seed;
- the network simply reproduces the latest month for every county.

### 10.3 Does it forecast better than the baseline?

For every target, calculate:

- county-level MAE;
- county-level RMSE;
- county-level WAPE;
- county-level MASE where a valid seasonal-naive scale exists;
- statewide August absolute percentage error;
- number of outer August folds that beat seasonal naive.

MAPE should not be the main county metric because small counties can create extreme percentages. WAPE and MASE are more informative at county level. Retain the official competition metric when it becomes available.

### 10.4 Is the result stable?

Repeat the locked configuration with seeds 1, 7, and 42. Record the mean, standard deviation, best, and worst result. A model that wins under only one seed is not reliable evidence.

## 11. Acceptance rule

N-BEATS should be called a qualified challenger only if all of the following are true for a target:

1. It beats seasonal naive on the chosen primary aggregate metric on average.
2. It wins in more than one of the three August folds.
3. Its gain does not come entirely from one exceptional year.
4. County-level WAPE or MASE is not materially worse.
5. Results are reasonably stable across seeds.
6. Every cutoff and missing-data audit passes.

The existing pipeline uses an even stricter replacement rule: lower mean MAPE and a win in all three folds. We should show results under that locked rule as well. If N-BEATS fails it, it remains an experimental benchmark and does not replace seasonal naive.

## 12. Implementation sequence for our next coding session

### Stage A: tiny learning example

Use a short artificial monthly series or the standard AirPassengers example to learn:

- `unique_id`, `ds`, and `y` long format;
- the difference between `input_size` and `h`;
- fitting, predicting, and plotting;
- how one sliding window becomes one learning example.

Success means we can manually identify the exact 12 input values used for one prediction.

### Stage B: statewide project prototype

Use `forecast_august_2026/results/monthly_series.csv` and fit one target at a time. This is for understanding the code, not for claiming strong deep-learning evidence: one 55-month series is very small.

Success means the prototype reproduces the cutoff logic and writes one forecast per fold without leakage.

### Stage C: global county-panel model

Convert `food_county_month_clean.csv` to `unique_id`, `ds`, `y`, exclude Wilkin for the documented structural reason, and train one global model per target.

Success means all eligible counties receive a forecast and their sum produces the statewide prediction.

### Stage D: locked backtest and seed study

Run the three outer August folds and three seeds. Save fold-level county predictions, aggregate predictions, metrics, parameters, software versions, and cutoff audits.

### Stage E: final decision

Compare N-BEATS with seasonal naive under the same data definitions and cutoff. Keep N-BEATS only if it satisfies the acceptance rule.

## 13. Planned code structure

Keeping data preparation, modeling, and evaluation separate will make the example easier to learn and audit.

```text
forecasting_pipeline/
  nbeats/
    README.md
    prepare_nbeats_data.py
    train_nbeats.py
    evaluate_nbeats.py
    run_nbeats_backtest.py
    results/
      config.json
      county_predictions.csv
      statewide_predictions.csv
      metrics.csv
      cutoff_audit.txt
```

Each file should have one job:

- `prepare_nbeats_data.py`: validate dates, targets, missingness, and long format.
- `train_nbeats.py`: construct and fit the model from an explicit configuration.
- `evaluate_nbeats.py`: compute metrics and baseline comparisons.
- `run_nbeats_backtest.py`: orchestrate cutoff-safe folds and save artifacts.

## 14. Minimal code shape—not the final implementation

This snippet shows the library interface we will learn. It intentionally omits the project's fold-safe missing-data preparation and backtest loop, so it must not be used as the final result by itself.

```python
from neuralforecast import NeuralForecast
from neuralforecast.losses.pytorch import MAE
from neuralforecast.models import NBEATS

model = NBEATS(
    h=1,
    input_size=12,
    stack_types=["identity"],
    n_blocks=[2],
    mlp_units=[[64, 64]],
    shared_weights=True,
    loss=MAE(),
    valid_loss=MAE(),
    scaler_type="robust",
    learning_rate=1e-3,
    max_steps=500,
    val_check_steps=25,
    early_stop_patience_steps=5,
    batch_size=32,
    windows_batch_size=256,
    random_seed=1,
)

forecaster = NeuralForecast(models=[model], freq="MS")
forecaster.fit(df=train_long, val_size=3)
predictions = forecaster.predict()
```

Before running this on project data, we will verify the library's expected monthly frequency convention and missing-value/mask behavior in the installed version. The final script will pin the dependency version so future runs do not silently change behavior.

## 15. What not to do

- Do not randomly split rows.
- Do not tune on August 2023, 2024, or 2025 and then report those same months as unbiased tests.
- Do not use `input_size=24` in the earliest fold unless the padding experiment is explicitly separate.
- Do not use the library's large default network without justification.
- Do not fill Wilkin with zero.
- Do not replace missing targets with values calculated from future months.
- Do not judge success from training loss or an in-sample plot.
- Do not report only the best random seed.
- Do not compare county N-BEATS error with a differently defined statewide baseline.

## 16. Learning resources in recommended order

1. [3Blue1Brown: But what is a neural network?](https://www.youtube.com/watch?v=aircAruvnKk) — visual foundation for layers, weights, activations, and outputs.
2. [3Blue1Brown: Gradient descent, how neural networks learn](https://www.youtube.com/watch?v=IHZwWFHWa-w) — why training changes weights and what the learning rate is doing.
3. [Forecasting: Principles and Practice — time-series cross-validation](https://otexts.com/fpp3/tscv.html) — why future observations cannot enter training.
4. [Original N-BEATS paper](https://arxiv.org/abs/1905.10437) — first read the abstract, Figure 1, Sections 3.1–3.3, and the conclusion; do not try to absorb every experiment initially.
5. [Official ServiceNow N-BEATS repository](https://github.com/servicenow/n-beats) — reference implementation associated with the research project.
6. [Nixtla NeuralForecast quickstart](https://nixtlaverse.nixtla.io/neuralforecast/docs/getting-started/quickstart.html) — learn the `unique_id`, `ds`, `y`, `fit`, and `predict` interface.
7. [Nixtla N-BEATS model documentation](https://nixtlaverse.nixtla.io/neuralforecast/models.nbeats.html) — current parameters and a runnable example.
8. [NeuralForecast cross-validation documentation](https://nixtlaverse.nixtla.io/neuralforecast/docs/capabilities/cross_validation.html) — useful after the manual fold logic is understood.

## 17. Questions you should be able to answer before implementation

1. Why is a random train/test split invalid here?
2. What values enter a 12-month window that predicts August?
3. What is the difference between `input_size=12` and `h=1`?
4. Why can a global model learn from multiple counties while remaining univariate?
5. What do a block's backcast and forecast represent?
6. Why do we scale county series?
7. Why is MAE preferable to MAPE as the first training loss?
8. What is the difference between validation loss and outer August test error?
9. Why must Wilkin remain structural missing instead of zero?
10. What evidence would justify keeping N-BEATS over seasonal naive?

If these answers are clear, the next step is Stage A: build a very small example, inspect its sliding windows, and explain each line before applying it to the Minnesota data.
