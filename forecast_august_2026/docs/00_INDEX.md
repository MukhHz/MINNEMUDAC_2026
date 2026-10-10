# August 2026 Forecasting Documentation

Updated: October 10, 2026

This documentation describes the complete forecasting work performed for the
August 2026 Minnesota food-shelf prediction task. It covers the data definition,
preprocessing, leakage controls, engineered features, models, backtesting,
evaluation metrics, selected forecasts, limitations, and reproducibility.

## Documentation files

1. [Executive summary](01_EXECUTIVE_SUMMARY.md)
   - What was done
   - Main findings
   - Selected August 2026 forecasts

2. [Data and preprocessing](02_DATA_AND_PREPROCESSING.md)
   - Input datasets
   - Target definition
   - Data-scope discrepancy
   - Missing values, scaling, transformations, and leakage controls

3. [Feature engineering and models](03_FEATURE_ENGINEERING_AND_MODELS.md)
   - Engineered predictors
   - Baseline, statistical, regularized, tree, structural, and ensemble models
   - Models intentionally not used

4. [Validation, results, and selection](04_VALIDATION_RESULTS_AND_SELECTION.md)
   - Rolling-origin evaluation
   - Meaning of 2/3 and 3/3 fold wins
   - Model-by-model MAPE comparison
   - Final selection logic

5. [Reproducibility and artifacts](05_REPRODUCIBILITY_AND_ARTIFACTS.md)
   - How to rerun the analysis
   - Software versions
   - Output-file descriptions
   - Verification performed

## Primary implementation

- Modeling script: `../advanced_forecasting.py`
- Executed analysis notebook: `../Advanced_Forecasting_Analysis.ipynb`
- Generated outputs: `../advanced_results/`
- Original baseline pipeline: `../forecast.py`

## Current selected hold forecasts

| Target | Selected model | August 2026 forecast |
|---|---|---:|
| Visits | Seasonal naive | **240,280** |
| Pounds distributed | Seasonal naive | **12,821,474.42** |
| Individuals served | Core median ensemble | **721,409.79** |

These are hold forecasts, not final competition submissions. The official
scoring rule and the target scope—particularly whether meal-program rows should
be included—must be confirmed before submission.

