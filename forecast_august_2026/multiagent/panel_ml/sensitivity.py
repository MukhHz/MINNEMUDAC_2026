"""Post-hoc diagnostics (NOT used for model choice): paired comparison vs damped_yoy_3m,
monthly MAPE by year, mmf_select n_inner sensitivity, and selected-candidate shares."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import harness, models as M

out = HERE / "results"
p = pd.read_csv(out / "predictions.csv")
mo = p[p.protocol == "monthly"].copy()
mo["year"] = pd.to_datetime(mo.target_month).dt.year
base = mo[mo.model == "damped_yoy_3m"].set_index(["metric", "target_month"]).ape
rows = []
for (met, mod), g in mo.groupby(["metric", "model"]):
    a = g.set_index(["metric", "target_month"]).ape
    d = (a - base.loc[a.index])
    r = dict(metric=met, model=mod, monthly_mape=a.mean(), wins_vs_damped=int((d < 0).sum()),
             mean_diff_pp=100 * d.mean(), t_stat=d.mean() / (d.std(ddof=1) / np.sqrt(len(d))) if d.std() > 0 else np.nan)
    for y, gy in g.groupby("year"):
        r[f"mape_{y}"] = gy.ape.mean()
    rows.append(r)
pt = pd.DataFrame(rows).sort_values(["metric", "monthly_mape"])
pt.to_csv(out / "paired_vs_damped.csv", index=False)

# n_inner sensitivity for mmf_select (monthly + august)
sens = []
targets = list(harness.MONTHLY_ORIGINS) + [pd.Timestamp(y, 8, 1) for y in harness.AUGUST_YEARS]
act = harness.load_monthly().set_index("month")
share = {}
for level in ("county", "food_bank", "site"):
    for n in (3, 6, 12):
        f = M.make_mmf_select(level, n_inner=n)
        for met in harness.METRICS:
            apes_m, apes_a = [], []
            for t in targets:
                ctx = harness.make_context(t, met)
                e = abs(f(ctx) / act.loc[t, met] - 1)
                (apes_m if t in harness.MONTHLY_ORIGINS else apes_a).append(e)
            sens.append(dict(level=level, n_inner=n, metric=met, monthly_mape=np.mean(apes_m), aug_mape=np.mean(apes_a)))
s = pd.DataFrame(sens).pivot_table(index=["metric", "level"], columns="n_inner", values=["monthly_mape", "aug_mape"])
s.to_csv(out / "mmf_ninner_sensitivity.csv")

# which candidates are selected (volume-weighted) at county level, final origin
cands = ("snaive", "damped50", "yoy_full", "recent_mean", "seasonal_level")
lines = []
for t in [pd.Timestamp("2024-08-01"), pd.Timestamp("2025-08-01"), harness.FINAL_TARGET]:
    for met in harness.METRICS:
        ctx = harness.make_context(t, met)
        for level in ("county", "food_bank"):
            _, Y, _, units = M.panel(ctx, level)
            i = len(Y); err = np.zeros((5, Y.shape[1]))
            for j in range(i - 6, i):
                for c, nm in enumerate(cands):
                    err[c] += np.abs(M.LOCAL_CANDS[nm](Y, j) - Y[j])
            b = err.argmin(0); w = Y[i - 12:i].sum(0)
            sh = {nm: round(w[b == c].sum() / w.sum(), 2) for c, nm in enumerate(cands)}
            lines.append(f"{t.date()} {met:11s} {level:9s} volume share selected: {sh}")
(out / "mmf_selected_shares.txt").write_text("\n".join(lines) + "\n")
pd.set_option("display.width", 250)
print(pt.round(4).to_string(index=False)); print(s.round(4).to_string()); print("\n".join(lines))
