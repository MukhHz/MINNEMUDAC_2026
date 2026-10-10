"""Statistical / local univariate models for the multi-agent August study.

Every model is predict(ctx) -> float and uses only ctx.y (months < target).
All hyper-parameters are either fixed a priori (stated in the name/docstring)
or selected INSIDE the model by an inner rolling one-step evaluation on
months before the cutoff (damped_yoy_auto).
"""
from __future__ import annotations

import warnings
from collections import defaultdict

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
np.random.seed(0)

from statsforecast.models import AutoARIMA, AutoCES, AutoETS, AutoTheta, MSTL  # noqa: E402

MIN_SEASONAL_OBS = 24          # need two full seasons for seasonal statsforecast models
FALLBACKS: dict[str, list] = defaultdict(list)   # model -> [(target, metric, reason)]
SELECTIONS: list[dict] = []


def _snaive(y: pd.Series, t: pd.Timestamp) -> float:
    return float(y.loc[t - pd.DateOffset(years=1)])


def _fallback(name, ctx, reason):
    FALLBACKS[name].append((ctx.target_month.date(), ctx.metric, reason))
    return _snaive(ctx.y, ctx.target_month)


# ------------------------------------------------------------------ statsforecast on levels / logs
def _sf(name, make_model, log=True, min_obs=MIN_SEASONAL_OBS):
    def predict(ctx):
        y = ctx.y.dropna()
        if len(y) < min_obs:
            return _fallback(name, ctx, f"n={len(y)}<{min_obs}")
        arr = np.log(y.values) if log else y.values.astype(float)
        try:
            f = float(make_model().forecast(y=arr, h=1)["mean"][0])
        except Exception as exc:  # noqa: BLE001
            return _fallback(name, ctx, f"fit error {type(exc).__name__}")
        f = float(np.exp(f)) if log else f
        if not np.isfinite(f) or f <= 0:
            return _fallback(name, ctx, "non-finite forecast")
        return f
    predict.__name__ = name
    return predict


sf_ets_log = _sf("sf_ets_log", lambda: AutoETS(season_length=12))
sf_ets_level = _sf("sf_ets_level", lambda: AutoETS(season_length=12), log=False)
sf_arima_log = _sf("sf_arima_log", lambda: AutoARIMA(season_length=12))
sf_theta_log = _sf("sf_theta_log", lambda: AutoTheta(season_length=12))
sf_ces_log = _sf("sf_ces_log", lambda: AutoCES(season_length=12))
sf_mstl_log = _sf("sf_mstl_log", lambda: MSTL(season_length=12, trend_forecaster=AutoETS(model="ZZN")))


# ------------------------------------------------------------------ YoY log-ratio models
def _log_ratio(y: pd.Series) -> pd.Series:
    return np.log(y / y.shift(12)).dropna()


def _ratio_model(name, fc_fn, min_ratio_obs=6):
    """Forecast r = log(y_t / y_{t-12}) one step ahead, then y_hat = y_{t-12} * exp(r_hat)."""
    def predict(ctx):
        y, t = ctx.y, ctx.target_month
        r = _log_ratio(y)
        if len(r) < min_ratio_obs:
            return _fallback(name, ctx, f"ratio n={len(r)}<{min_ratio_obs}")
        try:
            rh = float(fc_fn(r.values.astype(float)))
        except Exception as exc:  # noqa: BLE001
            return _fallback(name, ctx, f"fit error {type(exc).__name__}")
        if not np.isfinite(rh):
            return _fallback(name, ctx, "non-finite")
        return _snaive(y, t) * float(np.exp(rh))
    predict.__name__ = name
    return predict


ratio_ses = _ratio_model("ratio_ses", lambda r: AutoETS(model="ANN").forecast(y=r, h=1)["mean"][0])
ratio_ets_auto = _ratio_model("ratio_ets_auto", lambda r: AutoETS(model="ZZN").forecast(y=r, h=1)["mean"][0])
ratio_arima = _ratio_model("ratio_arima", lambda r: AutoARIMA(seasonal=False).forecast(y=r, h=1)["mean"][0])
ratio_theta = _ratio_model("ratio_theta", lambda r: AutoTheta().forecast(y=r, h=1)["mean"][0])
# fixed a priori shrinkage: half of the mean of the last 3 log-ratios
ratio_mean3_half = _ratio_model("ratio_mean3_half", lambda r: 0.5 * np.mean(r[-3:]), min_ratio_obs=3)


# ------------------------------------------------------------------ damped-YoY family
def _damped_yoy(y: pd.Series, t: pd.Timestamp, w: int, d: float) -> float:
    win = pd.date_range(t - pd.DateOffset(months=w), periods=w, freq="MS")
    g = y.loc[win].sum() / y.loc[[m - pd.DateOffset(years=1) for m in win]].sum()
    return float(y.loc[t - pd.DateOffset(years=1)] * (1 + d * (g - 1)))


WINDOWS = (1, 3, 6, 12)
DAMPS = (0.25, 0.5, 0.75, 1.0)


def make_damped(w, d):
    def predict(ctx):
        return _damped_yoy(ctx.y, ctx.target_month, w, d)
    predict.__name__ = f"dyoy_w{w}_d{d}"
    return predict


DAMPED_GRID = {f"dyoy_w{w}_d{d}": make_damped(w, d) for w in WINDOWS for d in DAMPS}


def damped_yoy_auto(ctx, n_inner=12, min_inner=3):
    """Select (w, d) from WINDOWS x {0}+DAMPS by inner 1-step MAPE over the last
    n_inner origins before the cutoff (each inner forecast uses only data before its
    own inner target).  Falls back to (3, 0.5) when < min_inner origins exist."""
    y, t = ctx.y, ctx.target_month
    first = y.index.min()
    grid = [(w, d) for w in WINDOWS for d in (0.0,) + DAMPS]
    origins = [t - pd.DateOffset(months=k) for k in range(n_inner, 0, -1)]
    scores = {}
    for w, d in grid:
        errs = []
        for o in origins:
            if o - pd.DateOffset(years=1, months=w) < first:
                continue
            errs.append(abs(_damped_yoy(y[y.index < o], o, w, d) / y.loc[o] - 1))
        if len(errs) >= min_inner:
            scores[(w, d)] = np.mean(errs)
    if not scores:
        FALLBACKS["damped_yoy_auto"].append((t.date(), ctx.metric, "no inner origins -> (3,0.5)"))
        w, d = 3, 0.5
    else:
        w, d = min(scores, key=scores.get)
    SELECTIONS.append(dict(model="damped_yoy_auto", target=t.date(), metric=ctx.metric, choice=f"w{w}_d{d}"))
    return _damped_yoy(y, t, w, d)


# ------------------------------------------------------------------ level-corrected seasonal models
def snaive_level12(ctx):
    """Geometric level correction: y_{t-12} * exp(mean log YoY ratio over last 12 months)
    (fixed a priori; up to 12 ratios, fewer when history is short)."""
    y, t = ctx.y, ctx.target_month
    r = _log_ratio(y)
    if len(r) < 1:
        return _fallback("snaive_level12", ctx, "no ratios")
    return _snaive(y, t) * float(np.exp(r.iloc[-12:].mean()))


def seasonal_index_level(ctx):
    """Level = mean of last 12 months; multiplicative seasonal index for the target
    calendar month = mean over past years of y_m / trailing-12-month mean ending at m-1."""
    y, t = ctx.y, ctx.target_month
    trail = y.rolling(12).mean()
    idx = []
    for m in y.index:
        p = m - pd.DateOffset(months=1)
        if m.month == t.month and p in trail.index and np.isfinite(trail.loc[p]):
            idx.append(y.loc[m] / trail.loc[p])
    if not idx:
        return _fallback("seasonal_index_level", ctx, "no seasonal index")
    return float(y.iloc[-12:].mean() * np.mean(idx))


# ------------------------------------------------------------------ fixed a-priori combinations
def _combo(name, members, how="median"):
    def predict(ctx):
        vals = np.array([m(ctx) for m in members], dtype=float)
        vals = vals[np.isfinite(vals)]
        return float(np.median(vals) if how == "median" else np.mean(vals))
    predict.__name__ = name
    return predict


combo_stat_median = _combo("combo_stat_median", [sf_ets_log, sf_theta_log, ratio_ses, damped_yoy_auto])
combo_ratio_mean = _combo("combo_ratio_mean", [ratio_ses, ratio_arima, ratio_theta], how="mean")


MODELS = {
    "sf_ets_log": sf_ets_log, "sf_ets_level": sf_ets_level, "sf_arima_log": sf_arima_log,
    "sf_theta_log": sf_theta_log, "sf_ces_log": sf_ces_log, "sf_mstl_log": sf_mstl_log,
    "ratio_ses": ratio_ses, "ratio_ets_auto": ratio_ets_auto, "ratio_arima": ratio_arima,
    "ratio_theta": ratio_theta, "ratio_mean3_half": ratio_mean3_half,
    **DAMPED_GRID,
    "damped_yoy_auto": damped_yoy_auto,
    "snaive_level12": snaive_level12, "seasonal_index_level": seasonal_index_level,
    "combo_stat_median": combo_stat_median, "combo_ratio_mean": combo_ratio_mean,
}
