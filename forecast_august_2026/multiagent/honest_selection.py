"""Selection-bias check: re-run the selection procedure online.

At each monthly origin t (from 2025-01), rank candidates using ONLY their
errors on earlier origins (< t), take the top-k from distinct agents,
average their forecasts for t, and score. This estimates how the
'pick the best of ~100 models' procedure performs out of sample.
"""
import pandas as pd, numpy as np
from combine import load_all

p = load_all()
p = p[~p.model.str.startswith("baselines:")] if False else p
mo = p[p.protocol == "monthly"].copy()
mo["t"] = pd.to_datetime(mo.target_month)
fin = p[p.protocol == "final"]
rows = []
for metric in ["visits", "pounds", "individuals"]:
    m = mo[mo.metric == metric]
    wide = m.pivot_table(index="t", columns="model", values="prediction")
    act = m.groupby("t").actual.first()
    agent = {c: c.split(":")[0] for c in wide.columns}
    for t in wide.index[wide.index >= "2025-01-01"]:
        past = wide.index < t
        ape = (wide[past].div(act[past], axis=0) - 1).abs().mean().dropna().sort_values()
        for k in (1, 3, 5):
            chosen, seen = [], set()
            for c in ape.index:
                if agent[c] not in seen and agent[c] != "baselines":
                    chosen.append(c); seen.add(agent[c])
                if len(chosen) == k: break
            pred = wide.loc[t, chosen].mean()
            rows.append((metric, t, f"online_top{k}", abs(pred / act[t] - 1)))
        for c in ["baselines:seasonal_naive", "baselines:damped_yoy_3m"]:
            rows.append((metric, t, c.split(":")[1], abs(wide.loc[t, c] / act[t] - 1)))
r = pd.DataFrame(rows, columns=["metric", "t", "method", "ape"])
r.to_csv("honest_selection_detail.csv", index=False)
out = r.groupby(["metric", "method"]).ape.agg(["mean", "median"]).unstack(0).round(4)
aug = r[r.t == "2025-08-01"].pivot(index="method", columns="metric", values="ape").round(4)
print("Online-selection MAPE, 19 origins Jan 2025-Jul 2026:\n", out, "\n\nAug 2025 fold:\n", aug)
