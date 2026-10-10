"""Shared leakage-safe evaluation harness for the multi-agent August study.

Every model is a callable

    predict(ctx: ForecastContext) -> float

that receives ONLY information available at the cutoff (end of the month
before ``ctx.target_month``).  The harness slices the data, asserts the
cutoff, calls the model, and only then looks up the actual for scoring.

Protocols
---------
A  "august"  : official Question 7 folds -- forecast Aug 2023/2024/2025
               from data through July 31 of that year.
B  "monthly" : robustness check -- 1-step-ahead forecast of every month
               Jan 2024 .. Jul 2026 (31 origins).  Same horizon as the
               August task, ten times more evaluation points.
Final        : forecast Aug 2026 from data through July 31, 2026.
"""

from __future__ import annotations

import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]          # MINNEMUDAC_2026
SITE_FILE = ROOT / "Data" / "processed" / "foodshelf_site_month.csv"
METRICS = ("visits", "pounds", "individuals")
AUGUST_YEARS = (2023, 2024, 2025)
MONTHLY_ORIGINS = pd.date_range("2024-01-01", "2026-07-01", freq="MS")
FINAL_TARGET = pd.Timestamp("2026-08-01")
HARD_CUTOFF = pd.Timestamp("2026-07-31")


@dataclass(frozen=True)
class ForecastContext:
    target_month: pd.Timestamp      # first day of the month to forecast
    metric: str                     # visits | pounds | individuals
    monthly: pd.DataFrame           # statewide totals, months < target_month
    site: pd.DataFrame              # site-month rows, months < target_month

    @property
    def cutoff(self) -> pd.Timestamp:
        return self.target_month - pd.Timedelta(days=1)

    @property
    def y(self) -> pd.Series:
        """Statewide series for ctx.metric indexed by month (MS)."""
        return self.monthly.set_index("month")[self.metric].asfreq("MS")


_SITE_CACHE: pd.DataFrame | None = None


def load_site() -> pd.DataFrame:
    global _SITE_CACHE
    if _SITE_CACHE is None:
        site = pd.read_csv(SITE_FILE, parse_dates=["month"], low_memory=False)
        assert site["month"].max() <= HARD_CUTOFF, "source contains data after 2026-07-31"
        _SITE_CACHE = site
    return _SITE_CACHE


def load_monthly() -> pd.DataFrame:
    site = load_site()
    monthly = (site.groupby("month", as_index=False)[list(METRICS)]
               .sum(min_count=1).sort_values("month").reset_index(drop=True))
    monthly["year"] = monthly["month"].dt.year
    monthly["month_num"] = monthly["month"].dt.month
    return monthly


def make_context(target_month: pd.Timestamp, metric: str) -> ForecastContext:
    monthly, site = load_monthly(), load_site()
    m = monthly[monthly["month"] < target_month].copy()
    s = site[site["month"] < target_month].copy()
    # ---- written, executable cutoff checks ----
    expected_last = target_month - pd.DateOffset(months=1)
    assert m["month"].max() == expected_last, f"monthly train ends {m['month'].max()} not {expected_last}"
    assert s["month"].max() <= expected_last, "site train exceeds cutoff"
    assert not (m["month"] == target_month).any(), "target month leaked into training"
    assert target_month <= FINAL_TARGET
    return ForecastContext(target_month, metric, m.reset_index(drop=True), s.reset_index(drop=True))


def _targets(protocol: str) -> list[pd.Timestamp]:
    if protocol == "august":
        return [pd.Timestamp(y, 8, 1) for y in AUGUST_YEARS]
    if protocol == "monthly":
        return list(MONTHLY_ORIGINS)
    if protocol == "final":
        return [FINAL_TARGET]
    raise ValueError(protocol)


def evaluate(models: dict[str, Callable[[ForecastContext], float]], out_dir: str | Path,
             protocols=("august", "monthly", "final"), metrics=METRICS) -> pd.DataFrame:
    """Run every model under every protocol; write predictions + summary."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    monthly_all = load_monthly().set_index("month")
    rows = []
    for protocol in protocols:
        for target in _targets(protocol):
            for metric in metrics:
                ctx = make_context(target, metric)
                for name, fn in models.items():
                    t0 = time.time()
                    try:
                        pred, err = float(fn(ctx)), ""
                    except Exception as exc:  # keep going; record failure
                        pred, err = np.nan, f"{type(exc).__name__}: {exc}"
                        traceback.print_exc(file=sys.stderr)
                    # actual is looked up only AFTER the prediction exists
                    actual = float(monthly_all.loc[target, metric]) if protocol != "final" else np.nan
                    rows.append(dict(protocol=protocol, target_month=target.date(), metric=metric,
                                     model=name, prediction=pred, actual=actual,
                                     ape=abs(pred / actual - 1) if actual == actual else np.nan,
                                     seconds=round(time.time() - t0, 2), error=err))
    pred = pd.DataFrame(rows)
    pred.to_csv(out / "predictions.csv", index=False)
    summ = summarize(pred)
    summ.to_csv(out / "summary.csv", index=False)
    (out / "cutoff_check.txt").write_text(
        "PASS every training slice ends the month before its target (asserted in make_context)\n"
        "PASS actuals retrieved only after each prediction was produced\n"
        f"PASS source max month <= {HARD_CUTOFF.date()}; no August 2026 data loaded\n")
    return summ


def summarize(pred: pd.DataFrame) -> pd.DataFrame:
    p = pred[pred["protocol"] != "final"].copy()
    p["year"] = pd.to_datetime(p["target_month"]).dt.year
    out = []
    for (metric, model), g in p.groupby(["metric", "model"]):
        a = g[g.protocol == "august"].set_index("year")["ape"]
        mo = g[g.protocol == "monthly"]["ape"]
        fin = pred[(pred.protocol == "final") & (pred.metric == metric) & (pred.model == model)]["prediction"]
        out.append(dict(metric=metric, model=model,
                        aug_mape=a.mean(), aug_2023=a.get(2023), aug_2024=a.get(2024), aug_2025=a.get(2025),
                        aug_mape_2024_25=a.drop(2023, errors="ignore").mean(),
                        monthly_mape=mo.mean(), monthly_median_ape=mo.median(), monthly_n=int(mo.notna().sum()),
                        forecast_aug_2026=fin.iloc[0] if len(fin) else np.nan))
    return pd.DataFrame(out).sort_values(["metric", "monthly_mape"])


# ---------------- reference baselines every agent must beat ----------------
def seasonal_naive(ctx: ForecastContext) -> float:
    return float(ctx.y.loc[ctx.target_month - pd.DateOffset(years=1)])


def damped_yoy_3m(ctx: ForecastContext, damping: float = 0.5) -> float:
    y, t = ctx.y, ctx.target_month
    w = pd.date_range(t - pd.DateOffset(months=3), periods=3, freq="MS")
    g = y.loc[w].sum() / y.loc[[d - pd.DateOffset(years=1) for d in w]].sum()
    return float(y.loc[t - pd.DateOffset(years=1)] * (1 + damping * (g - 1)))


# ---------------- the five models Question 7 requires ----------------
# Written for any target month; for an August target they are exactly the Q7 definitions.
def ytd_growth(ctx: ForecastContext) -> float:
    """Same month last year x year-to-date growth (Jan..cutoff month vs same months last year).
    For a January target the trailing 12-month growth is used."""
    y, t = ctx.y, ctx.target_month
    last = t - pd.DateOffset(months=1)
    start = pd.Timestamp(last.year, 1, 1) if t.month > 1 else last - pd.DateOffset(months=11)
    cur = y.loc[start:last].sum()
    prev = y.loc[start - pd.DateOffset(years=1):last - pd.DateOffset(years=1)].sum()
    return float(y.loc[t - pd.DateOffset(years=1)] * cur / prev)


def aug_jul_ratio(ctx: ForecastContext) -> float:
    """Last month x median historical (target month / previous month) ratio.
    For August this is July x the median August/July ratio before the cutoff."""
    y, t = ctx.y, ctx.target_month
    ratios = []
    k = t - pd.DateOffset(years=1)
    while k - pd.DateOffset(months=1) >= y.index.min():
        ratios.append(y.loc[k] / y.loc[k - pd.DateOffset(months=1)])
        k -= pd.DateOffset(years=1)
    return float(y.loc[t - pd.DateOffset(months=1)] * np.median(ratios))


def trend_month_regression(ctx: ForecastContext) -> float:
    """OLS with a linear trend and month-of-year indicators."""
    y = ctx.y
    t = np.arange(len(y))
    month = y.index.month.to_numpy()
    X = np.column_stack([np.ones(len(y)), t] + [(month == m).astype(float) for m in range(2, 13)])
    x_new = np.array([1.0, len(y)] + [float(ctx.target_month.month == m) for m in range(2, 13)])
    beta, *_ = np.linalg.lstsq(X, y.to_numpy(float), rcond=None)
    return float(x_new @ beta)


def robust_ensemble(ctx: ForecastContext) -> float:
    """Median of the four models above."""
    return float(np.median([f(ctx) for f in (seasonal_naive, ytd_growth, aug_jul_ratio,
                                             trend_month_regression)]))


BASELINES = {"seasonal_naive": seasonal_naive, "damped_yoy_3m": damped_yoy_3m,
             "ytd_growth": ytd_growth, "aug_jul_ratio": aug_jul_ratio,
             "trend_month_regression": trend_month_regression, "robust_ensemble": robust_ensemble}

if __name__ == "__main__":
    s = evaluate(BASELINES, Path(__file__).parent / "baselines" / "results")
    pd.set_option("display.width", 200)
    print(s.round(4).to_string(index=False))
