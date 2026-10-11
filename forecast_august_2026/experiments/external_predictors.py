"""External-predictor experiments (all rejected; none is used by the final model).

1. MN county SNAP enrolment (Data/processed/snap_2022_2026_clean.csv), 5-month lag
2. MN DHS SNAP dashboard (Data/external/...), persons and benefit per person, 2- and 4-month lags
3. Incoming calls (Data/Incoming Call.xlsx), statewide, effect fitted on past data only

For the SNAP tests each predictor is (a) applied as a ratio to seasonal naive and (b) offered
as an extra candidate in the county-by-county selection, so a county uses it only where it has
worked over the previous 12 months.  Every forecast for target month t uses predictor values
dated at least LAG months before t, and never after July 2026.

Run from forecast_august_2026/:  python experiments/external_predictors.py
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

DATA = ms.ROOT / "Data"
OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
CUTOFF = pd.Timestamp("2026-07-31")
site = ms.load_site()
TARGETS = ([("august", pd.Timestamp(y, 8, 1)) for y in (2023, 2024, 2025)]
           + [("monthly", t) for t in pd.date_range("2024-01-01", "2026-07-01", freq="MS")])


def growth(P, t, counties, lag, w=3):
    """County YoY growth of predictor P over the latest w months available at target t."""
    last = t - pd.DateOffset(months=lag)
    assert last <= CUTOFF
    idx = pd.date_range(last - pd.DateOffset(months=w - 1), last, freq="MS")
    g = P.reindex(idx).sum() / P.reindex([d - pd.DateOffset(years=1) for d in idx]).sum()
    return g.reindex(counties).replace([np.inf, 0], np.nan).fillna(1.0).clip(0.7, 1.3).to_numpy()


def snap_experiment(name, predictors, lags):
    """predictors: {label: (wide county panel, direction)}; direction +1 multiplies, -1 divides."""
    rows = []
    for proto, t in TARGETS:
        for m in ms.COLUMNS.values():
            Y, counties = ms.county_panel(site, m, t)
            i = len(Y)
            fc = ms.forecast(site, m, t)
            act = (site[site.month == t].groupby("county_key")[m].sum()
                   .reindex(counties).fillna(0.0).to_numpy())
            sn = fc["seasonal_naive"].to_numpy()
            preds = {"final_current": fc["final"].to_numpy()}
            for lag in lags:
                extra_now, extra_fn = [], []
                for label, (P, sign) in predictors.items():
                    g = growth(P, t, counties, lag) ** sign
                    preds[f"naive_x_{label}_lag{lag}"] = sn * g
                    extra_now.append(sn * g)
                    extra_fn.append((P, sign))
                if i - ms.N_SELECT >= 12:
                    cands = list(ms.SELECT_CANDIDATES.values())
                    err = np.zeros((len(cands) + len(extra_fn), Y.shape[1]))
                    for j in range(i - ms.N_SELECT, i):
                        tj = t - pd.DateOffset(months=i - j)
                        with np.errstate(divide="ignore", invalid="ignore"):
                            for c, f in enumerate(cands):
                                err[c] += np.abs(f(Y, j) - Y[j])
                        for k, (P, sign) in enumerate(extra_fn):
                            err[len(cands) + k] += np.abs(Y[j - 12] * growth(P, tj, counties, lag) ** sign - Y[j])
                    with np.errstate(divide="ignore", invalid="ignore"):
                        allfc = np.vstack([np.stack([f(Y, i) for f in cands])] + extra_now)
                    preds[f"final_plus_snap_lag{lag}"] = allfc[err.argmin(0), np.arange(Y.shape[1])]
                else:
                    preds[f"final_plus_snap_lag{lag}"] = fc["final"].to_numpy()
            for k, p in preds.items():
                rows.append(dict(proto=proto, t=t, metric=m, model=k,
                                 wape=np.abs(p - act).sum() / act.sum()))
    r = pd.DataFrame(rows)
    r["period"] = np.where(r.proto == "august", "Aug" + r.t.dt.year.astype(str), "mo" + r.t.dt.year.astype(str))
    tab = (r.pivot_table(index=["metric", "model"], columns="period", values="wape") * 100).round(2)
    tab["monthly_all"] = (r[r.proto == "monthly"].groupby(["metric", "model"]).wape.mean() * 100).round(2)
    tab.to_csv(OUT / f"{name}_county_wape.csv")
    lines = []
    for lag in lags:
        for m in ms.COLUMNS.values():
            w = r[(r.proto == "monthly") & (r.metric == m)].pivot(index="t", columns="model", values="wape")
            d = w[f"final_plus_snap_lag{lag}"] - w.final_current
            nz = d[d != 0]
            p = wilcoxon(nz).pvalue if len(nz) > 5 else float("nan")
            lines.append(f"{name} lag{lag} {m:12s} final+SNAP vs final: better {int((d < 0).sum())}, "
                         f"worse {int((d > 0).sum())}; mean {100 * d.mean():+.3f} pts; p={p:.3f}")
    return tab, lines


def calls_experiment():
    d = pd.read_excel(DATA / "Incoming Call.xlsx")
    d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
    assert d["Date"].max() <= CUTOFF
    calls = d.groupby(d.Date.dt.to_period("M").dt.to_timestamp()).size().astype(float)
    fs = site.groupby("month")[list(ms.COLUMNS.values())].sum()

    def yoy3(s, t, lag):
        w = pd.date_range(t - pd.DateOffset(months=lag + 2), t - pd.DateOffset(months=lag), freq="MS")
        return s.reindex(w).sum() / s.reindex([x - pd.DateOffset(years=1) for x in w]).sum() - 1

    rows = []
    for m in ms.COLUMNS.values():
        y = fs[m]
        for t in pd.date_range("2025-03-01", "2026-07-01", freq="MS"):
            ly, act = y[t - pd.DateOffset(years=1)], y[t]
            past = pd.date_range("2024-03-01", t - pd.DateOffset(months=1), freq="MS")
            X = np.array([yoy3(calls, s, 2) for s in past])
            Yv = np.array([y[s] / y[s - pd.DateOffset(years=1)] - 1 for s in past])
            b, a = np.polyfit(X, Yv, 1)            # fitted on months before t only
            preds = {"seasonal_naive": ly, "damped_yoy": ly * (1 + 0.5 * yoy3(y, t, 1)),
                     "calls_damped_lag2": ly * (1 + 0.5 * yoy3(calls, t, 2)),
                     "calls_regression_lag2": ly * (1 + a + b * yoy3(calls, t, 2))}
            for k, p in preds.items():
                rows.append((m, t, k, abs(p / act - 1)))
    r = pd.DataFrame(rows, columns=["metric", "t", "model", "ape"])
    tab = (r.pivot_table(index="model", columns="metric", values="ape") * 100).round(2)
    tab.to_csv(OUT / "calls_statewide_mape.csv")
    return tab


def main():
    pd.set_option("display.width", 220)
    summary = []

    snap = pd.read_csv(DATA / "processed" / "snap_2022_2026_clean.csv")
    snap["date"] = pd.to_datetime(snap.year.astype(str) + "-" + snap.month, format="%Y-%B")
    snap["county_key"] = snap.county.str.lower()
    P1 = snap.pivot_table(index="date", columns="county_key", values="snap_people", aggfunc="sum")
    tab, lines = snap_experiment("snap_county_repo", {"persons": (P1, 1)}, lags=(5,))
    print("SNAP (repo county file)\n", tab.to_string(), "\n")
    summary += lines

    dash = pd.read_excel(DATA / "external" / "snap-dashboard-data-through-september-2026.xlsx")
    dash["date"] = pd.to_datetime(dash.Report_Month)
    dash = dash[dash.date <= CUTOFF]                  # nothing after the cutoff is ever read
    dash["county_key"] = dash.CountyTribeName.str.lower().str.strip()
    persons = dash.pivot_table(index="date", columns="county_key", values="PersonCount", aggfunc="sum")
    benefit = dash.pivot_table(index="date", columns="county_key", values="Total_Net", aggfunc="sum")
    tab, lines = snap_experiment("snap_dashboard",
                                 {"persons": (persons, 1), "inv_persons": (persons, -1),
                                  "inv_benefit_per_person": (benefit / persons, -1)}, lags=(2, 4))
    print("SNAP dashboard\n", tab.to_string(), "\n")
    summary += lines

    tab = calls_experiment()
    print("Incoming calls, statewide MAPE (%), 17 origins Mar 2025 - Jul 2026\n", tab.to_string(), "\n")

    (OUT / "external_predictors_paired_tests.txt").write_text("\n".join(summary) + "\n")
    print("\n".join(summary))


if __name__ == "__main__":
    main()
