"""Final Aug 2026 forecast: equal-weight hedge of three model families.

  seasonal_naive            (baselines)  - last August, the seasonal anchor
  damped_yoy_3m             (baselines)  - last August x half of recent 3-month YoY growth
  mmf_select_county         (panel_ml)   - per-county local-model selection, summed

Interval: empirical quantiles of signed % errors of this same combination
over the 31 one-step monthly backtest origins (Jan 2024 - Jul 2026).
"""
import pandas as pd
from combine import load_all

MEMBERS = ["baselines:seasonal_naive", "baselines:damped_yoy_3m", "panel_ml:mmf_select_county"]
p = load_all()
s = (p[p.model.isin(MEMBERS)].groupby(["protocol", "target_month", "metric"])
     .agg(pred=("prediction", "mean"), act=("actual", "first"), n=("prediction", "count")).reset_index())
assert (s.n == len(MEMBERS)).all()
s["pct_err"] = s.act / s.pred - 1
rows = []
for m in ["visits", "pounds", "individuals"]:
    g = s[s.metric == m]
    e = g[g.protocol == "monthly"].pct_err
    fc = g[g.protocol == "final"].pred.iloc[0]
    rows.append(dict(metric=m, forecast=round(fc), lo80=round(fc * (1 + e.quantile(.10))),
                     hi80=round(fc * (1 + e.quantile(.90))),
                     backtest_monthly_mape=round((g[g.protocol == "monthly"].pred / g[g.protocol == "monthly"].act - 1).abs().mean(), 4),
                     backtest_aug_mape=round((g[g.protocol == "august"].pred / g[g.protocol == "august"].act - 1).abs().mean(), 4)))
out = pd.DataFrame(rows)
out.to_csv("final_forecast_aug_2026.csv", index=False)
print(out.to_string(index=False))
