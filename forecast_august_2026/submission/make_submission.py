"""County-level August 2026 forecast for the MinneMUDAC undergraduate submission.

Model (selected in ../multiagent, see ../multiagent/README.md): for every county,
the equal-weight mean of three local forecasts built from that county's
monthly totals (sum of its food-shelf sites):

  1. seasonal naive      : the county's August of the previous year
  2. damped 3-month YoY  : last August x (1 + 0.5 x (recent-3-month YoY growth - 1))
  3. MMF local selection : per county, whichever of {seasonal naive, damped YoY,
                           full YoY, recent 3-month mean, recent level x last-year
                           seasonal shape} had the lowest absolute error over the
                           last 6 one-step origins before the cutoff

Information cutoff: July 31, 2026.  The script refuses to run if the source holds
any later month, and every backtest fold is built only from months before its target.

Usage (from the MINNEMUDAC_2026 folder):
    python forecast_august_2026/submission/make_submission.py [--team-id ID]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SITE_FILE = ROOT / "Data" / "processed" / "foodshelf_site_month.csv"
TEMPLATE = ROOT / "Undergraduate_Predictions_Submit.csv"
OUT_DIR = Path(__file__).resolve().parent
CUTOFF = pd.Timestamp("2026-07-31")
TARGET = pd.Timestamp("2026-08-01")
# submission column -> prepared-data column
COLUMNS = {"HouseholdReg_Predicted": "visits",
           "PoundsReg_Predicted": "pounds",
           "IndividualsReg_Predicted": "individuals"}
DAMP, G_CLIP, N_INNER = 0.5, (0.0, 3.0), 6


# ---------------------------------------------------------------- data
def load_site() -> pd.DataFrame:
    site = pd.read_csv(SITE_FILE, parse_dates=["month"], low_memory=False)
    assert site["month"].max() <= CUTOFF, f"source has data after {CUTOFF.date()}"
    site["county_key"] = site["county"].str.lower()
    return site


def county_panel(site: pd.DataFrame, metric: str, target: pd.Timestamp):
    """Months x counties matrix built only from months strictly before target."""
    s = site[site["month"] < target]
    last = target - pd.DateOffset(months=1)
    assert s["month"].max() == last, "training slice must end the month before the target"
    months = pd.date_range(s["month"].min(), last, freq="MS")
    wide = (s.pivot_table(index="month", columns="county_key", values=metric, aggfunc="sum")
            .reindex(months).fillna(0.0))
    return wide.to_numpy(float), list(wide.columns)


# ---------------------------------------------------------------- local models
# Each takes Y (months x counties) and a target row index i, and reads rows < i only.
def snaive(Y, i):
    return Y[i - 12].copy()


def damped(Y, i, d=DAMP, w=3):
    ly, num, den = Y[i - 12], Y[i - w:i].sum(0), Y[i - 12 - w:i - 12].sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.clip(np.where(den > 0, num / den, 1.0), *G_CLIP)
    pred = ly * (1 + d * (g - 1))
    pred = np.where((ly <= 0) | (den <= 0), num / w, pred)   # new county series
    return np.where(num <= 0, 0.0, pred)                    # silent for 3 months


def recent_mean(Y, i, w=3):
    return Y[i - w:i].mean(0)


def seasonal_level(Y, i):
    den = Y[i - 15:i - 12].mean(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        shape = np.clip(np.where(den > 0, Y[i - 12] / den, 1.0), 0.5, 2.0)
    return Y[i - 3:i].mean(0) * shape


CANDIDATES = [snaive, damped, lambda Y, i: damped(Y, i, 1.0), recent_mean, seasonal_level]


def mmf_select(Y, i):
    origins = [j for j in range(i - N_INNER, i) if j >= 15]
    err = np.zeros((len(CANDIDATES), Y.shape[1]))
    for j in origins:
        for c, f in enumerate(CANDIDATES):
            err[c] += np.abs(f(Y, j) - Y[j])
    best = err.argmin(0) if origins else np.ones(Y.shape[1], int)
    fc = np.stack([f(Y, i) for f in CANDIDATES])
    return fc[best, np.arange(Y.shape[1])]


MODELS = {"seasonal_naive": snaive, "damped_yoy_3m": damped, "mmf_select": mmf_select}


def forecast(site, metric, target):
    Y, counties = county_panel(site, metric, target)
    i = len(Y)
    parts = {name: f(Y, i) for name, f in MODELS.items()}
    parts["blend"] = np.mean([parts[n] for n in MODELS], axis=0)
    return pd.DataFrame(parts, index=counties).clip(lower=0)


# ---------------------------------------------------------------- backtest
def backtest(site) -> pd.DataFrame:
    targets = ([("august", pd.Timestamp(y, 8, 1)) for y in (2023, 2024, 2025)]
               + [("monthly", t) for t in pd.date_range("2024-01-01", "2026-07-01", freq="MS")])
    rows = []
    for protocol, t in targets:
        for metric in COLUMNS.values():
            fc = forecast(site, metric, t)
            # actuals looked up only after the forecast exists
            act = (site[site["month"] == t].groupby("county_key")[metric].sum()
                   .reindex(fc.index).fillna(0.0))
            for model in fc.columns:
                e = fc[model] - act
                pos = act > 0
                rows.append(dict(protocol=protocol, target=t.date(), metric=metric, model=model,
                                 county_wape=e.abs().sum() / act.sum(),
                                 county_mape=(e[pos].abs() / act[pos]).mean(),
                                 county_median_ape=(e[pos].abs() / act[pos]).median(),
                                 county_rmse=float(np.sqrt((e ** 2).mean())),
                                 state_ape=abs(fc[model].sum() / act.sum() - 1)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--team-id", default="")
    args = ap.parse_args()

    site = load_site()
    bt = backtest(site)
    bt.to_csv(OUT_DIR / "county_backtest_detail.csv", index=False)
    summary = (bt.groupby(["metric", "model", "protocol"])
               [["county_wape", "county_mape", "county_median_ape", "county_rmse", "state_ape"]]
               .mean().round(4).reset_index())
    summary.to_csv(OUT_DIR / "county_backtest_summary.csv", index=False)

    # final forecast, fit on data through July 31, 2026
    template = pd.read_csv(TEMPLATE).dropna(subset=["County"])
    template["RowID"] = template["RowID"].astype(int)
    key = template["County"].str.lower()
    detail = []
    for col, metric in COLUMNS.items():
        fc = forecast(site, metric, TARGET)
        detail.append(fc.add_prefix(f"{metric}_"))
        # Wilkin has no food-shelf site in the data -> 0 predicted activity
        template[col] = key.map(fc["blend"]).fillna(0.0).round().astype(int)
    template["YourTeamID"] = args.team_id
    pd.concat(detail, axis=1).round(1).to_csv(OUT_DIR / "county_forecast_components.csv")

    missing = sorted(set(template.loc[~key.isin(fc.index), "County"]))
    unused = sorted(set(fc.index) - set(key))
    assert not unused, f"data counties missing from template: {unused}"
    out = OUT_DIR / "Undergraduate_Predictions_Submit.csv"
    template.to_csv(out, index=False)

    (OUT_DIR / "cutoff_check.txt").write_text(
        f"PASS source maximum month {site['month'].max():%Y-%m} <= {CUTOFF.date()}\n"
        "PASS every forecast (backtest and final) built from months strictly before its target\n"
        "PASS backtest actuals retrieved only after each forecast was produced\n"
        "PASS no external predictors used\n"
        f"NOTE counties with no food-shelf site, predicted 0: {missing}\n")

    pd.set_option("display.width", 200)
    print(summary.to_string(index=False))
    print("\nStatewide totals of submission:")
    print(template[list(COLUMNS)].sum().to_string())
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
