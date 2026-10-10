# Advanced August 2026 forecasting results

## Selection policy

The primary model remains seasonal naive unless a challenger has lower mean MAPE and beats it in all three August folds. SNAP sensitivity models are never eligible for primary selection because exact release dates are unverified.

## Statewide rolling-August comparison

| metric      | model                             |   mape |   median_ape |   wape |              mae |             rmse |   folds_better_than_naive | eligible_for_primary   |
|:------------|:----------------------------------|-------:|-------------:|-------:|-----------------:|-----------------:|--------------------------:|:-----------------------|
| individuals | ets                               |   4.69 |         3.5  |   4.66 |  34134.7         |  40507.5         |                         2 | True                   |
| individuals | lasso_panel                       |   6.28 |         6.94 |   6.29 |  46033.7         |  46650.4         |                         1 | True                   |
| individuals | core_median_ensemble              |   6.54 |         1.76 |   6.49 |  47529.6         |  73672.4         |                         3 | True                   |
| individuals | elastic_net_panel                 |   6.95 |         6.73 |   6.96 |  50926.5         |  51160.4         |                         1 | True                   |
| individuals | structural_elastic_visits_x_ratio |   7.21 |         4.69 |   7.19 |  52640.7         |  60983.4         |                         1 | True                   |
| individuals | sarima                            |   8.39 |         8.81 |   8.41 |  61582.6         |  64559.1         |                         1 | True                   |
| individuals | robust_ensemble                   |   9.4  |        10.24 |   9.43 |  69060.7         |  75028.6         |                         1 | True                   |
| individuals | ytd_growth                        |   9.69 |         2.52 |   9.83 |  71950.9         | 107893           |                         2 | True                   |
| individuals | aug_jul_ratio                     |  10.08 |        10.21 |  10.07 |  73713.6         |  86394.9         |                         1 | True                   |
| individuals | seasonal_naive                    |  10.49 |         2.86 |  10.43 |  76368.7         | 110721           |                         0 | True                   |
| individuals | ridge_panel                       |  13.61 |        12.18 |  13.69 | 100177           | 111169           |                         1 | True                   |
| individuals | trend_month_regression            |  15.47 |        17.2  |  15.48 | 113277           | 124352           |                         1 | True                   |
| individuals | lightgbm_panel                    |  21.42 |        20.17 |  21.42 | 156798           | 168311           |                         0 | True                   |
| individuals | lightgbm_panel_snap_sensitivity   |  21.65 |        19.21 |  21.64 | 158372           | 172738           |                         0 | False                  |
| pounds      | ridge_panel                       |   1.94 |         2.18 |   1.95 | 255216           | 308400           |                         2 | True                   |
| pounds      | structural_elastic_visits_x_ratio |   2.75 |         1.63 |   2.76 | 361365           | 514098           |                         2 | True                   |
| pounds      | core_median_ensemble              |   5.84 |         1.41 |   5.86 | 766488           |      1.14452e+06 |                         2 | True                   |
| pounds      | ets                               |   5.89 |         3.32 |   5.9  | 771076           |      1.00188e+06 |                         1 | True                   |
| pounds      | ytd_growth                        |   6.7  |         2.74 |   6.77 | 885491           |      1.29451e+06 |                         2 | True                   |
| pounds      | seasonal_naive                    |   7.03 |         3.23 |   7.05 | 921298           |      1.33235e+06 |                         0 | True                   |
| pounds      | robust_ensemble                   |   8.1  |         7.72 |   8.11 |      1.06e+06    |      1.16698e+06 |                         1 | True                   |
| pounds      | sarima                            |   8.69 |         2.11 |   8.75 |      1.14307e+06 |      1.81344e+06 |                         1 | True                   |
| pounds      | elastic_net_panel                 |   9.05 |        12.24 |   9.13 |      1.19318e+06 |      1.44e+06    |                         2 | True                   |
| pounds      | lasso_panel                       |   9.35 |        11.45 |   9.4  |      1.22826e+06 |      1.32262e+06 |                         1 | True                   |
| pounds      | aug_jul_ratio                     |   9.62 |        12.21 |   9.61 |      1.25613e+06 |      1.43142e+06 |                         1 | True                   |
| pounds      | trend_month_regression            |  10.2  |        11.19 |  10.16 |      1.32823e+06 |      1.42291e+06 |                         1 | True                   |
| pounds      | lightgbm_panel                    |  21.58 |        19.64 |  21.63 |      2.8277e+06  |      2.95389e+06 |                         0 | True                   |
| pounds      | lightgbm_panel_snap_sensitivity   |  21.78 |        18.7  |  21.83 |      2.85294e+06 |      2.9937e+06  |                         0 | False                  |
| visits      | lasso_panel                       |   4.37 |         5.27 |   4.36 |  10441.8         |  11877.7         |                         2 | True                   |
| visits      | elastic_net_panel                 |   5.52 |         4.87 |   5.5  |  13177.6         |  15282.5         |                         1 | True                   |
| visits      | core_median_ensemble              |   6.8  |         2.44 |   6.76 |  16195.4         |  22089.6         |                         1 | True                   |
| visits      | ets                               |   6.84 |         5.3  |   6.81 |  16314.4         |  18731.6         |                         1 | True                   |
| visits      | sarima                            |   6.88 |         6.7  |   6.89 |  16515.1         |  18208.3         |                         1 | True                   |
| visits      | seasonal_naive                    |   7.2  |         1.75 |   7.14 |  17115           |  26639.6         |                         0 | True                   |
| visits      | ytd_growth                        |   8.99 |         5.55 |   9.05 |  21680.7         |  30728.7         |                         1 | True                   |
| visits      | robust_ensemble                   |   9.15 |        12.1  |   9.19 |  22017.3         |  24766.4         |                         1 | True                   |
| visits      | ridge_panel                       |   9.36 |         8.85 |   9.31 |  22322.8         |  26921.8         |                         1 | True                   |
| visits      | aug_jul_ratio                     |  10.15 |         8.95 |  10.18 |  24400.3         |  30724.4         |                         1 | True                   |
| visits      | trend_month_regression            |  13.05 |        15.24 |  13.09 |  31367.1         |  35454.4         |                         1 | True                   |
| visits      | lightgbm_panel_snap_sensitivity   |  20.81 |        17.27 |  20.76 |  49755.5         |  53393.6         |                         0 | False                  |
| visits      | lightgbm_panel                    |  21.39 |        18.46 |  21.34 |  51144.3         |  54185.4         |                         0 | True                   |

## August 2026 forecasts

| metric      | model                             |         forecast | selected   | eligible_for_primary   |
|:------------|:----------------------------------|-----------------:|:-----------|:-----------------------|
| visits      | seasonal_naive                    | 240280           | True       | True                   |
| visits      | ytd_growth                        | 242520           | False      | True                   |
| visits      | aug_jul_ratio                     | 255519           | False      | True                   |
| visits      | trend_month_regression            | 289987           | False      | True                   |
| visits      | robust_ensemble                   | 249020           | False      | True                   |
| visits      | ets                               | 241363           | False      | True                   |
| visits      | sarima                            | 235154           | False      | True                   |
| visits      | ridge_panel                       | 238255           | False      | True                   |
| visits      | lasso_panel                       | 215284           | False      | True                   |
| visits      | elastic_net_panel                 | 222378           | False      | True                   |
| visits      | lightgbm_panel                    | 225114           | False      | True                   |
| visits      | lightgbm_panel_snap_sensitivity   | 223978           | False      | False                  |
| pounds      | seasonal_naive                    |      1.28215e+07 | True       | True                   |
| pounds      | ytd_growth                        |      1.32436e+07 | False      | True                   |
| pounds      | aug_jul_ratio                     |      1.38297e+07 | False      | True                   |
| pounds      | trend_month_regression            |      1.45257e+07 | False      | True                   |
| pounds      | robust_ensemble                   |      1.35366e+07 | False      | True                   |
| pounds      | ets                               |      1.26539e+07 | False      | True                   |
| pounds      | sarima                            |      1.30311e+07 | False      | True                   |
| pounds      | ridge_panel                       |      1.17193e+07 | False      | True                   |
| pounds      | lasso_panel                       |      1.11058e+07 | False      | True                   |
| pounds      | elastic_net_panel                 |      1.13962e+07 | False      | True                   |
| pounds      | lightgbm_panel                    |      1.22849e+07 | False      | True                   |
| pounds      | lightgbm_panel_snap_sensitivity   |      1.22094e+07 | False      | False                  |
| individuals | seasonal_naive                    | 724407           | False      | True                   |
| individuals | ytd_growth                        | 751854           | False      | True                   |
| individuals | aug_jul_ratio                     | 785547           | False      | True                   |
| individuals | trend_month_regression            | 889946           | False      | True                   |
| individuals | robust_ensemble                   | 768701           | False      | True                   |
| individuals | ets                               | 745285           | False      | True                   |
| individuals | sarima                            | 728024           | False      | True                   |
| individuals | ridge_panel                       | 756867           | False      | True                   |
| individuals | lasso_panel                       | 681786           | False      | True                   |
| individuals | elastic_net_panel                 | 718413           | False      | True                   |
| individuals | lightgbm_panel                    | 700953           | False      | True                   |
| individuals | lightgbm_panel_snap_sensitivity   | 701443           | False      | False                  |
| pounds      | structural_elastic_visits_x_ratio |      1.24473e+07 | False      | True                   |
| individuals | structural_elastic_visits_x_ratio | 677227           | False      | True                   |
| visits      | core_median_ensemble              | 232697           | False      | True                   |
| pounds      | core_median_ensemble              |      1.24694e+07 | False      | True                   |
| individuals | core_median_ensemble              | 721410           | True       | True                   |

## Selected hold forecast

- visits: 240,280.00 using `seasonal_naive`
- pounds: 12,821,474.42 using `seasonal_naive`
- individuals: 721,409.79 using `core_median_ensemble`

## Important limitations

- Only three historical August holdouts are available, so rankings are uncertain.
- County-panel models share information across counties but do not create additional years of statewide history.
- This experiment uses the newer clean export that excludes meal-program rows; do not mix its forecasts or metrics with the earlier locked baseline source that includes 2,702 meal rows.
- Reported outcomes are primary; site-imputed outcomes remain sensitivity data because masked-value validation error was high.
- Poverty and MMG variables are excluded from the primary experiment because their conservative availability rules do not provide a consistent feature history for the August 2023 fold.
- Deep learning is not included: four annual cycles are insufficient to justify it as a primary challenger.
