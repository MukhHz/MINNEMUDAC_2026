"""Part 1 data diagnostics (all data <= 2026-07-31). Writes CSVs to results/diag_*.csv
and prints a compact summary used in REPORT.md."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import harness  # noqa: E402
from models import norm_food_bank  # noqa: E402

OUT = HERE / "results"
OUT.mkdir(exist_ok=True)
pd.set_option("display.width", 220)
pd.set_option("display.max_columns", 40)

site = harness.load_site()
assert site.month.max() <= harness.HARD_CUTOFF
site = site.copy()
site["fb"] = norm_food_bank(site["food_bank"])
M = ["visits", "pounds", "individuals"]
rep = site[site.visits.notna()].copy()
W = rep.pivot_table(index="site_id", columns="month", values="visits", aggfunc="sum")
months = sorted(W.columns)
A = W.notna()
first = A.idxmax(axis=1)
last = A.iloc[:, ::-1].idxmax(axis=1)

# ---------------------------------------------------------------- (a) churn
rows = []
for i, m in enumerate(months):
    r = dict(month=m.date(), n_report=int(A[m].sum()))
    if i:
        p = months[i - 1]
        r["continuing"] = int((A[p] & A[m]).sum())
        r["entries"] = int((~A[p] & A[m]).sum())
        r["exits"] = int((A[p] & ~A[m]).sum())
        r["retention"] = r["continuing"] / A[p].sum()
        r["first_ever"] = int((first == m).sum())
        r["returning"] = r["entries"] - r["first_ever"]
        # of sites missing in m that reported in m-1: share that report again in m+1 (temporary gap)
        if i + 1 < len(months):
            gap = A[p] & ~A[m]
            r["gap_return_next"] = (A.loc[gap, months[i + 1]].mean() if gap.any() else np.nan)
            r["gap_return_ever"] = (A.loc[gap, months[i + 1:]].any(axis=1).mean() if gap.any() else np.nan)
        r["entry_mass_visits"] = W.loc[~A[p] & A[m], m].sum()
        r["exit_mass_visits"] = W.loc[A[p] & ~A[m], p].sum()
    rows.append(r)
churn = pd.DataFrame(rows)

# repeated-value (possible carry-forward) rows: all 3 metrics equal previous month
s2 = site.sort_values(["site_id", "month"]).copy()
prev = s2.groupby("site_id")[M + ["month"]].shift(1)
consec = (s2.month - prev.month).dt.days.between(27, 32)
s2["repeat"] = consec & (s2[M].eq(prev[M]).all(axis=1)) & s2.visits.notna()
churn["repeat_rows"] = churn.month.map(s2[s2.repeat].groupby(s2.month.dt.date).size()).fillna(0).astype(int)
churn["repeat_share"] = churn.repeat_rows / churn.n_report
churn.to_csv(OUT / "diag_churn_by_month.csv", index=False)

# July 2026 vs history: retention / count relative to trailing mean, and per-site mean
tot = rep.groupby("month")[M].sum()
nrep = rep.groupby("month").site_id.nunique()
per_site = tot.div(nrep, axis=0)
last_month_check = pd.DataFrame({
    "n_report": nrep, "n_vs_prev3": nrep / nrep.rolling(3).mean().shift(1),
    "visits_yoy": tot.visits.pct_change(12), "pounds_yoy": tot.pounds.pct_change(12),
    "indiv_yoy": tot.individuals.pct_change(12),
    "visits_per_site_yoy": per_site.visits.pct_change(12),
})
last_month_check.to_csv(OUT / "diag_last_month_check.csv")

# "reported" flag rows (site present but no numbers) by month -- possible late reporters
nonrep = site[site.visits.isna()].groupby("month").size()

# Sites that reported every month Jan-Jun 2026 and are missing in Jul 2026; same for prior years
def miss_last(year):
    ws = [pd.Timestamp(year, m, 1) for m in range(1, 7)]
    j = pd.Timestamp(year, 7, 1)
    core = A[ws].all(axis=1)
    return int(core.sum()), int((core & ~A[j]).sum()), float(W.loc[core & ~A[j], ws].mean(axis=1).sum())
core_miss = pd.DataFrame([dict(year=y, core_sites=a, core_missing_july=b, missing_jun_level_visits=c)
                          for y in (2023, 2024, 2025, 2026) for a, b, c in [miss_last(y)]])
core_miss.to_csv(OUT / "diag_core_missing_july.csv", index=False)

# ------------------------------------------------------- (b) shift-share
def shift_share(months_cur, metric):
    out = dict(cont_cur=0.0, cont_prev=0.0, entry=0.0, exit=0.0)
    Wm = rep.pivot_table(index="site_id", columns="month", values=metric, aggfunc="sum")
    for m in months_cur:
        p = m - pd.DateOffset(years=1)
        a = Wm[m] if m in Wm else pd.Series(dtype=float)
        b = Wm[p] if p in Wm else pd.Series(dtype=float)
        both = a.notna() & b.notna()
        out["cont_cur"] += a[both].sum(); out["cont_prev"] += b[both].sum()
        out["entry"] += a[a.notna() & b.isna()].sum()
        out["exit"] += b[b.notna() & a.isna()].sum()
    prev_tot = out["cont_prev"] + out["exit"]
    cur_tot = out["cont_cur"] + out["entry"]
    return dict(prev_total=prev_tot, cur_total=cur_tot, yoy=cur_tot / prev_tot - 1,
                same_site_contrib=(out["cont_cur"] - out["cont_prev"]) / prev_tot,
                entry_contrib=out["entry"] / prev_tot, exit_contrib=-out["exit"] / prev_tot,
                same_site_growth=out["cont_cur"] / out["cont_prev"] - 1,
                share_prev_mass_continuing=out["cont_prev"] / prev_tot)

ss_rows = []
periods = {
    "Aug2023": [pd.Timestamp(2023, 8, 1)], "Aug2024": [pd.Timestamp(2024, 8, 1)],
    "Aug2025": [pd.Timestamp(2025, 8, 1)],
    "CY2023": list(pd.date_range("2023-01-01", "2023-12-01", freq="MS")),
    "CY2024": list(pd.date_range("2024-01-01", "2024-12-01", freq="MS")),
    "CY2025": list(pd.date_range("2025-01-01", "2025-12-01", freq="MS")),
    "Jan-Jul2026": list(pd.date_range("2026-01-01", "2026-07-01", freq="MS")),
    "May-Jul2026": list(pd.date_range("2026-05-01", "2026-07-01", freq="MS")),
    "Jul2026": [pd.Timestamp(2026, 7, 1)],
}
for name, ms in periods.items():
    for met in M:
        ss_rows.append(dict(period=name, metric=met, **shift_share(ms, met)))
ss = pd.DataFrame(ss_rows)
ss.to_csv(OUT / "diag_shift_share.csv", index=False)

# -------------------------------------------------- (c) August seasonality
def ratios(series_by_month, label):
    r = []
    for y in range(2022, 2026):
        a, j = pd.Timestamp(y, 8, 1), pd.Timestamp(y, 7, 1)
        mj = [pd.Timestamp(y, m, 1) for m in (5, 6, 7)]
        r.append(dict(group=label, year=y, aug_jul=series_by_month.get(a) / series_by_month.get(j),
                      aug_mayjul=series_by_month.get(a) / np.mean([series_by_month.get(x) for x in mj])))
    return r

seas = []
for met in M:
    for rr in ratios(tot[met].to_dict(), "STATEWIDE"):
        seas.append(dict(metric=met, **rr))
    fbt = rep.groupby(["fb", "month"])[met].sum()
    for fb in sorted(rep.fb.unique()):
        d = fbt.loc[fb].to_dict()
        if all(pd.Timestamp(y, m, 1) in d for y in range(2022, 2026) for m in (5, 6, 7, 8)):
            for rr in ratios(d, fb):
                seas.append(dict(metric=met, **rr))
    # matched panel: sites reporting May-Aug of that year
    for y in range(2022, 2026):
        cols = [pd.Timestamp(y, m, 1) for m in (5, 6, 7, 8)]
        Wm = rep.pivot_table(index="site_id", columns="month", values=met, aggfunc="sum")[cols].dropna()
        seas.append(dict(metric=met, group="MATCHED_PANEL", year=y,
                         aug_jul=Wm[cols[3]].sum() / Wm[cols[2]].sum(),
                         aug_mayjul=Wm[cols[3]].sum() / Wm[cols[:3]].sum(axis=0).mean()))
seas = pd.DataFrame(seas)
seas.to_csv(OUT / "diag_august_seasonality.csv", index=False)
seas_stats = (seas.groupby(["metric", "group"])[["aug_jul", "aug_mayjul"]]
              .agg(["mean", "std", "min", "max"]).round(3))
seas_stats.to_csv(OUT / "diag_august_seasonality_stats.csv")

# ---------------------------------------------- (d) flag sensitivity (Aug)
sens = []
s2["any_flag"] = s2[["flag_outlier", "flag_dup_summed", "flag_typo_fixed"]].any(axis=1)
for y in (2022, 2023, 2024, 2025):
    a = pd.Timestamp(y, 8, 1)
    g = s2[s2.month == a]
    for met in M:
        base = g[met].sum()
        sens.append(dict(year=y, metric=met, total=base,
                         pct_outlier=g.loc[g.flag_outlier, met].sum() / base,
                         pct_dup_summed=g.loc[g.flag_dup_summed, met].sum() / base,
                         pct_typo_fixed=g.loc[g.flag_typo_fixed, met].sum() / base,
                         pct_hh_gt_indiv=g.loc[g.flag_hh_gt_indiv, met].sum() / base,
                         pct_repeat=g.loc[g.repeat, met].sum() / base,
                         n_outlier=int(g.flag_outlier.sum()), n_repeat=int(g.repeat.sum())))
sens = pd.DataFrame(sens)
# effect on YoY Aug growth if outlier+repeat rows were dropped
for met in M:
    for y in (2023, 2024, 2025):
        a, b = pd.Timestamp(y, 8, 1), pd.Timestamp(y - 1, 8, 1)
        keep = ~(s2.flag_outlier | s2.repeat)
        yoy_all = s2.loc[s2.month == a, met].sum() / s2.loc[s2.month == b, met].sum() - 1
        yoy_k = s2.loc[(s2.month == a) & keep, met].sum() / s2.loc[(s2.month == b) & keep, met].sum() - 1
        sens.loc[(sens.year == y) & (sens.metric == met), "yoy_all"] = yoy_all
        sens.loc[(sens.year == y) & (sens.metric == met), "yoy_drop_outlier_repeat"] = yoy_k
sens.to_csv(OUT / "diag_flag_sensitivity_aug.csv", index=False)
# repeat share in July 2026 vs earlier (carry-forward at the edge?)
rep_by_month = churn.set_index("month")[["repeat_rows", "repeat_share"]]
jul26 = s2[(s2.month == "2026-07-01")]
jul_rep_pct = {met: jul26.loc[jul26.repeat, met].sum() / jul26[met].sum() for met in M}
flag_by_month = s2.groupby("month")[["flag_outlier", "repeat"]].sum().tail(8)

if __name__ == "__main__":
    print("=== (a) churn, last 14 months ===")
    print(churn.tail(14).round(3).to_string(index=False))
    print("\nmean retention 2024-01..2026-06:",
          round(churn[(churn.month >= pd.Timestamp("2024-01-01").date()) &
                      (churn.month < pd.Timestamp("2026-07-01").date())].retention.mean(), 4),
          " Jul2026:", round(churn.iloc[-1].retention, 4))
    print("mean gap_return_next (2024-2026/05):",
          round(churn[churn.month >= pd.Timestamp("2024-01-01").date()].gap_return_next.mean(), 3))
    print("\nlast-month check (tail 8):\n", last_month_check.tail(8).round(3).to_string())
    print("\nrows present but no numbers, tail:\n", nonrep.tail(8).to_string())
    print("\ncore (all Jan-Jun) sites missing July:\n", core_miss.to_string(index=False))
    print("\n=== (b) shift-share ===")
    print(ss.round(4).to_string(index=False))
    print("\n=== (c) August seasonality ===")
    print(seas[seas.group.isin(["STATEWIDE", "MATCHED_PANEL"])].round(3).to_string(index=False))
    print(seas_stats.to_string())
    print("\n=== (d) flag sensitivity (Aug) ===")
    print(sens.round(4).to_string(index=False))
    print("\nrepeat share by month tail:\n", rep_by_month.tail(8).round(3).to_string())
    print("Jul 2026 repeat-row mass share:", {k: round(v, 4) for k, v in jul_rep_pct.items()})
    print("flags tail:\n", flag_by_month.to_string())


# ------------------------------------------ (a2) within-site partial-month check
def drop_profile(year, metric="visits"):
    Wm = rep.pivot_table(index="site_id", columns="month", values=metric, aggfunc="sum")
    j, base = pd.Timestamp(year, 7, 1), [pd.Timestamp(year, m, 1) for m in (4, 5, 6)]
    sub = Wm[base + [j]].dropna()
    lvl = sub[base].mean(axis=1)
    sub = sub[lvl > 0]
    r = sub[j] / sub[base].mean(axis=1)
    return dict(year=year, metric=metric, n=len(sub), share_drop_gt50=(r < 0.5).mean(),
                share_zero_july=(sub[j] == 0).mean(), median_ratio=r.median(),
                agg_ratio=sub[j].sum() / sub[base].mean(axis=1).sum())
drops = pd.DataFrame([drop_profile(y, m) for m in M for y in (2022, 2023, 2024, 2025, 2026)])
drops.to_csv(OUT / "diag_july_within_site_drops.csv", index=False)

# concentration of Jul 2026 YoY visits change among matched sites
Wv = rep.pivot_table(index="site_id", columns="month", values="visits", aggfunc="sum")
a, b = pd.Timestamp(2026, 7, 1), pd.Timestamp(2025, 7, 1)
both = Wv[[a, b]].dropna()
delta = (both[a] - both[b]).sort_values()
conc = dict(total_matched_change=delta.sum(), top10_negative=delta.head(10).sum(),
            top10_positive=delta.tail(10).sum(), n_matched=len(delta))
repeat_zero = s2[s2.repeat]
repeat_zero_share = (repeat_zero.visits == 0).mean()

if __name__ == "__main__":
    print("\n=== (a2) within-site July drop profile (Jul vs Apr-Jun mean, sites reporting all 4) ===")
    print(drops.round(3).to_string(index=False))
    print("Jul26 vs Jul25 matched-site visits change concentration:", {k: round(v) for k, v in conc.items()})
    print("share of repeat rows that are zero-visit rows:", round(repeat_zero_share, 3))
