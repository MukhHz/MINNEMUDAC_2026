# Pre-registered selection rule (written before any agent results were seen)

Date: 2026-10-10. Applies to every candidate in `multiagent/*/results/predictions.csv`.

## Evidence used
- **Protocol A (official):** August 2023, 2024, 2025 folds, cutoff July 31 of each year.
- **Protocol B (robustness):** 31 one-step-ahead monthly forecasts, Jan 2024 – Jul 2026,
  the same 1-month horizon as the August task.
- The 2023 fold is in the 2022–23 ramp-up regime; it is reported but given less weight.

## A challenger replaces seasonal naive for a metric only if ALL hold
1. Monthly MAPE (Protocol B) at least 1 percentage point lower than seasonal naive.
2. Mean August MAPE (Protocol A) lower than seasonal naive.
3. Mean APE on the August 2024–25 folds no more than 1.5 points worse than seasonal naive.
4. Fit failures on 0 of the 34 origins (or a documented, cutoff-safe fallback).

## Choosing among the challengers that qualify
- Prefer a **fixed-weight equal mean of the top qualifying models from different agents**
  (at most 3, ranked by Protocol B MAPE) over any single model, because
  equal weights involve no fitting to the evaluation folds.
- Adopt the combination only if it also satisfies rules 1–3; otherwise use the single best qualifying model.
- If nothing qualifies, keep seasonal naive.

## Multiple-comparison caveat
Many variants are tested. Protocol B differences under about 1 point are treated as noise.
The final report lists every model tried, not just the winners.
