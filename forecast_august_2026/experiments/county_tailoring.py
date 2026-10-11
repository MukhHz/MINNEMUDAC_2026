"""County-tailoring experiments that led to the final county-by-county model.

Compares, at county level and under the same cutoff rules as the submission:
  A  current blend applied to every county
  B  site-level blend summed to counties (handles site entry/exit)
  C  B with one-off spikes in last year's value capped
  D  county-by-county selection (= the submitted `final` model)
and reports WAPE by period, a full metric set for A vs D, and paired Wilcoxon tests.

Run from forecast_august_2026/:  python experiments/county_tailoring.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "submission"))
import make_submission as ms  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
site = ms.load_site()
site["sid"] = site["site_id"].astype(int)


def site_panel(metric, target):
    s = site[site.month < target]
    months = pd.date_range(s.month.min(), target - pd.DateOffset(months=1), freq="MS")
    W = (s.pivot_table(index="month", columns="sid", values=metric, aggfunc="sum")
         .reindex(months).fillna(0.0))
    county_of = s.groupby("sid")["county_key"].last().reindex(W.columns)
    return W.to_numpy(float), county_of.to_numpy()


def site_blend(Y, i, robust=False):
    ly = Y[i - 12].copy()
    rec = Y[i - 3:i].mean(0)
    if robust:  # cap last year's value to [0.5, 2] x the site's surrounding-year median
        med = np.median(Y[max(0, i - 18):i - 6], axis=0)
        ly = np.where(med > 0, np.clip(ly, 0.5 * med, 2.0 * med), ly)
    new = (ly <= 0) & (rec > 0)          # opened since last year
    gone = Y[i - 3:i].sum(0) <= 0        # silent 3 months -> closed
    Yr = Y.copy()
    Yr[i - 12] = ly
    with np.errstate(divide="ignore", invalid="ignore"):
        parts = [np.where(new, rec, ly), np.where(new, rec, ms.damped(Yr, i)),
                 np.where(new, rec, ms.mmf_select(Yr, i))]
    return np.where(gone, 0.0, np.mean(parts, axis=0))


def main():
    rows = []
    targets = ([("august", pd.Timestamp(y, 8, 1)) for y in (2023, 2024, 2025)]
               + [("monthly", t) for t in pd.date_range("2024-01-01", "2026-07-01", freq="MS")])
    for proto, t in targets:
        for m in ms.COLUMNS.values():
            Y, counties = ms.county_panel(site, m, t)
            fc = ms.forecast(site, m, t)
            Ys, cof = site_panel(m, t)
            preds = {"A_blend_all_counties": fc["blend"].to_numpy(),
                     "D_county_by_county_FINAL": fc["final"].to_numpy()}
            for rb, name in [(False, "B_site_level_blend"), (True, "C_site_level_blend_capped")]:
                v = pd.Series(site_blend(Ys, len(Ys), rb)).groupby(cof).sum()
                preds[name] = v.reindex(counties).fillna(0.0).to_numpy()
            act = (site[site.month == t].groupby("county_key")[m].sum()
                   .reindex(counties).fillna(0.0).to_numpy())
            prev = Y[len(Y) - 12]
            for k, p in preds.items():
                e = p - act
                pos = act > 0
                ape = np.abs(e[pos]) / act[pos]
                rows.append(dict(proto=proto, t=t, metric=m, model=k,
                                 WAPE=np.abs(e).sum() / act.sum(), MAPE=ape.mean(), MdAPE=np.median(ape),
                                 MAE=np.abs(e).mean(), RMSE=np.sqrt((e ** 2).mean()),
                                 Bias=e.sum() / act.sum(),
                                 RelMAE_vs_naive=np.abs(e).sum() / np.abs(prev - act).sum(),
                                 State_APE=abs(p.sum() / act.sum() - 1)))
    r = pd.DataFrame(rows)
    r.to_csv(OUT / "county_tailoring_detail.csv", index=False)

    r["period"] = np.where(r.proto == "august", "Aug" + r.t.dt.year.astype(str), "mo" + r.t.dt.year.astype(str))
    by_period = (r.pivot_table(index=["metric", "model"], columns="period", values="WAPE") * 100).round(2)
    by_period["monthly_all"] = (r[r.proto == "monthly"].groupby(["metric", "model"]).WAPE.mean() * 100).round(2)
    by_period.to_csv(OUT / "county_tailoring_wape_by_period.csv")

    metrics = r[r.proto == "monthly"].groupby(["metric", "model"])[
        ["WAPE", "MAPE", "MdAPE", "MAE", "RMSE", "Bias", "RelMAE_vs_naive", "State_APE"]].mean()
    metrics.to_csv(OUT / "county_tailoring_metrics_monthly.csv")

    lines = []
    for m in ms.COLUMNS.values():
        w = r[(r.proto == "monthly") & (r.metric == m)].pivot(index="t", columns="model", values="WAPE")
        d = w.D_county_by_county_FINAL - w.A_blend_all_counties
        lines.append(f"{m:12s} final better in {int((d < 0).sum())}/31 months; mean diff "
                     f"{100 * d.mean():+.2f} pts; Wilcoxon p={wilcoxon(d[d != 0]).pvalue:.3f}")
    (OUT / "county_tailoring_paired_test.txt").write_text("\n".join(lines) + "\n")

    pd.set_option("display.width", 220)
    print("County WAPE (%) by period\n", by_period.to_string(), "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
