"""Panel / many-model / global-ML forecasters for the multi-agent August study.

Every public model is ``predict(ctx) -> float`` (statewide total), built only
from ``ctx.site`` / ``ctx.y`` (months < ctx.target_month).

Unit panels are built by summing site rows (NaN -> 0) by unit and month, so the
unit totals sum exactly to ``ctx.y`` (verified in run.py).

Hyper-parameters are fixed a priori (listed below) or chosen by an inner,
past-only backtest inside ctx.  Nothing is tuned on the harness folds.
"""

from __future__ import annotations

import warnings
from functools import lru_cache

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

SEED = 0
DAMP = 0.5            # a-priori damping (same as reference baseline)
G_CLIP = (0.0, 3.0)   # clip on unit-level YoY growth factors
Z_CLIP = 1.0          # clip on unit-level log-YoY training targets

LGB_PARAMS = dict(n_estimators=300, learning_rate=0.03, num_leaves=8, min_child_samples=30,
                  subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                  random_state=SEED, verbose=-1, n_jobs=1, deterministic=True, force_col_wise=True)
RIDGE_ALPHA = 1.0


# --------------------------------------------------------------------------- panels
def _unit_key(site: pd.DataFrame, level: str) -> pd.Series:
    if level == "county":
        return site["fips"]
    if level == "food_bank":
        return site["food_bank"].str.replace("*", "", regex=False).str.replace(" Inc.", "", regex=False).str.strip()
    if level == "site":
        return site["site_id"]
    if level == "site_group":
        return site["site_group"]
    raise ValueError(level)


def _ctx_key(ctx):
    return (ctx.target_month, ctx.metric)


_PANEL_CACHE: dict = {}


def panel(ctx, level: str, metric: str | None = None):
    """Return (months, Y[M,U], N[M,U], units).  Y = unit sums (NaN->0), N = reporting sites."""
    metric = metric or ctx.metric
    key = (ctx.target_month, metric, level)
    if key in _PANEL_CACHE:
        return _PANEL_CACHE[key]
    s = ctx.site
    months = pd.date_range(s["month"].min(), ctx.target_month - pd.DateOffset(months=1), freq="MS")
    df = pd.DataFrame({"u": _unit_key(s, level).values, "month": s["month"].values,
                       "y": s[metric].fillna(0.0).values,
                       "n": (s["reported"] & s[metric].notna()).astype(int).values})
    Y = df.pivot_table(index="month", columns="u", values="y", aggfunc="sum").reindex(months).fillna(0.0)
    N = df.pivot_table(index="month", columns="u", values="n", aggfunc="sum").reindex(months).fillna(0.0)
    N = N.reindex(columns=Y.columns).fillna(0.0)
    out = (months, Y.values.astype(float), N.values.astype(float), list(Y.columns))
    if len(_PANEL_CACHE) > 4000:
        _PANEL_CACHE.clear()
    _PANEL_CACHE[key] = out
    return out


# --------------------------------------------------------------------------- local candidates
# each takes the wide array Y (months x units) and a target index i (may be <= len(Y));
# it only reads rows < i, returns a forecast vector per unit.
def loc_snaive(Y, i):
    return Y[i - 12].copy()


def loc_damped(Y, i, d=DAMP, w=3):
    ly = Y[i - 12]
    num = Y[i - w:i].sum(0)
    den = Y[i - 12 - w:i - 12].sum(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        g = np.clip(np.where(den > 0, num / den, 1.0), *G_CLIP)
    pred = ly * (1 + d * (g - 1))
    new = (ly <= 0) | (den <= 0)          # unit absent last year -> recent mean level
    pred = np.where(new, num / w, pred)
    pred = np.where(num <= 0, 0.0, pred)  # unit gone silent for w months -> 0
    return pred


def loc_recent_mean(Y, i, w=3):
    return Y[i - w:i].mean(0)


def loc_seasonal_level(Y, i):
    """recent 3m level x last-year seasonal shape (Y[i-12] / mean Y[i-15:i-12])."""
    den = Y[i - 15:i - 12].mean(0)
    with np.errstate(divide="ignore", invalid="ignore"):
        s = np.clip(np.where(den > 0, Y[i - 12] / den, 1.0), 0.5, 2.0)
    return Y[i - 3:i].mean(0) * s


LOCAL_CANDS = {
    "snaive": loc_snaive,
    "damped50": lambda Y, i: loc_damped(Y, i, 0.5),
    "yoy_full": lambda Y, i: loc_damped(Y, i, 1.0),
    "recent_mean": loc_recent_mean,
    "seasonal_level": loc_seasonal_level,
}


def make_bottom_up(level: str, cand: str):
    f = LOCAL_CANDS[cand]

    def predict(ctx):
        months, Y, N, units = panel(ctx, level)
        return float(f(Y, len(Y)).sum())
    predict.__name__ = f"bu_{cand}_{level}"
    return predict


def make_mmf_select(level: str, n_inner: int = 6, cands=("snaive", "damped50", "yoy_full", "recent_mean", "seasonal_level")):
    """Databricks-MMF style: per unit, pick the local model with lowest abs error on
    the last n_inner one-step origins inside ctx (past only), then sum."""
    def predict(ctx):
        months, Y, N, units = panel(ctx, level)
        i = len(Y)
        origins = [j for j in range(i - n_inner, i) if j >= 15]
        err = np.zeros((len(cands), Y.shape[1]))
        for j in origins:
            for c, name in enumerate(cands):
                err[c] += np.abs(LOCAL_CANDS[name](Y, j) - Y[j])
        best = err.argmin(0) if origins else np.ones(Y.shape[1], int)
        fc = np.stack([LOCAL_CANDS[n](Y, i) for n in cands])
        return float(fc[best, np.arange(Y.shape[1])].sum())
    predict.__name__ = f"mmf_select_{level}"
    return predict


def make_inner_tuned_damped(level: str, n_inner: int = 12, grid=(0.0, 0.25, 0.5, 0.75, 1.0)):
    """Bottom-up damped YoY with damping chosen by statewide APE over the last
    n_inner one-step origins inside ctx."""
    def predict(ctx):
        months, Y, N, units = panel(ctx, level)
        i = len(Y)
        tot = Y.sum(1)
        origins = [j for j in range(i - n_inner, i) if j >= 15]
        if not origins:
            d = DAMP
        else:
            scores = [np.mean([abs(loc_damped(Y, j, d).sum() / tot[j] - 1) for j in origins]) for d in grid]
            d = grid[int(np.argmin(scores))]
        return float(loc_damped(Y, i, d).sum())
    predict.__name__ = f"bu_damped_tuned_{level}"
    return predict


# --------------------------------------------------------------------------- ETS per unit
def make_ets(level: str):
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    def predict(ctx):
        months, Y, N, units = panel(ctx, level)
        i = len(Y)
        if i < 24:  # not enough for a seasonal ETS -> local damped YoY
            return float(loc_damped(Y, i).sum())
        tot = 0.0
        for u in range(Y.shape[1]):
            y = Y[:, u]
            if y[-3:].sum() <= 0:
                continue
            if (y[-24:] <= 0).any():          # intermittent unit -> damped YoY
                tot += loc_damped(Y[:, [u]], i)[0]
                continue
            ly = np.log(y[-36:] if i >= 36 else y)
            try:
                m = ExponentialSmoothing(ly, trend="add", damped_trend=True, seasonal="add",
                                         seasonal_periods=12, initialization_method="estimated").fit()
                f1 = float(np.exp(m.forecast(1)[0]))
                if not np.isfinite(f1):
                    raise ValueError("non-finite ETS forecast")
                tot += f1
            except Exception:
                tot += loc_damped(Y[:, [u]], i)[0]
        return float(tot)
    predict.__name__ = f"ets_{level}"
    return predict


# --------------------------------------------------------------------------- global models on log-YoY ratio
FEATS = ["z1", "z2", "z3", "g3", "g6", "ly_mom", "lvl", "dn", "ln_n", "zs1", "gs3", "moy"]


def _features(Y, N, months, site_level: bool):
    """Return feature dict of arrays (M,U) and target z (M,U).  Row m features use rows < m only."""
    M, U = Y.shape
    if site_level:
        L = np.where(Y > 0, np.log(np.where(Y > 0, Y, 1.0)), np.nan)
    else:
        L = np.log(Y + 1.0)
    z = np.full((M, U), np.nan)
    z[12:] = L[12:] - L[:-12]
    nanarr = lambda: np.full((M, U), np.nan)
    F = {k: nanarr() for k in FEATS}
    C = np.vstack([np.zeros((1, U)), np.cumsum(Y, 0)])          # C[k] = sum Y[:k]
    tot = Y.sum(1)
    Ct = np.concatenate([[0.0], np.cumsum(tot)])
    Ls = np.log(tot)
    for m in range(13, M + 1):
        r = m  # feature row index (may equal M for prediction)
        row = {}
        row["z1"] = z[m - 1]
        row["z2"] = z[m - 2] if m - 2 >= 12 else np.full(U, np.nan)
        row["z3"] = z[m - 3] if m - 3 >= 12 else np.full(U, np.nan)
        if m >= 15:
            s3, s3l = C[m] - C[m - 3], C[m - 12] - C[m - 15]
            row["g3"] = np.log((s3 + 1) / (s3l + 1))
            row["gs3"] = np.full(U, np.log((Ct[m] - Ct[m - 3]) / (Ct[m - 12] - Ct[m - 15])))
        if m >= 18:
            s6, s6l = C[m] - C[m - 6], C[m - 12] - C[m - 18]
            row["g6"] = np.log((s6 + 1) / (s6l + 1))
        row["ly_mom"] = L[m - 12] - L[m - 13]
        row["lvl"] = np.log((C[m] - C[max(m - 12, 0)]) / min(12, m) + 1)
        row["dn"] = np.log((N[m - 1] + 1) / (N[m - 13] + 1))
        row["ln_n"] = np.log(N[m - 1] + 1)
        row["zs1"] = np.full(U, Ls[m - 1] - Ls[m - 13])
        row["moy"] = np.full(U, float(((months[0].month - 1 + m) % 12) + 1))
        F_row = row
        if r == M:
            pred_row = F_row
        else:
            for k, v in F_row.items():
                F[k][r] = v
    return F, pred_row, z


def _fit_predict(kind, Xtr, ytr, wtr, Xte):
    if kind == "lgbm":
        import lightgbm as lgb
        mdl = lgb.LGBMRegressor(**LGB_PARAMS)
        mdl.fit(Xtr, ytr, sample_weight=wtr)
        return mdl.predict(Xte)
    if kind == "ridge":
        from sklearn.linear_model import Ridge
        def prep(X):
            X = X.copy()
            moy = X[:, -1].astype(int)
            X = np.nan_to_num(X[:, :-1], nan=0.0)
            oh = np.eye(12)[moy - 1]
            return X, oh
        A, oha = prep(Xtr)
        B, ohb = prep(Xte)
        mu, sd = A.mean(0), A.std(0) + 1e-9
        A, B = np.hstack([(A - mu) / sd, oha]), np.hstack([(B - mu) / sd, ohb])
        mdl = Ridge(alpha=RIDGE_ALPHA).fit(A, ytr, sample_weight=wtr)
        return mdl.predict(B)
    raise ValueError(kind)


def make_global(level: str, kind: str = "lgbm", window: int | None = None, churn: bool = False):
    """Global model across units on z = log(y_t / y_{t-12}).

    statewide forecast = sum_u y_{u,t-12} * exp(zhat_u) (+ recent-mean level for
    units absent last year; 0 for units silent the last 3 months).
    churn=True (site level): forecast = Y_{t-12} * G_matched * c, where G_matched is
    the y_{t-12}-weighted mean predicted ratio over sites still active, and c is the
    mean churn factor (Y_m / (Y_{m-12} * matched growth_m)) of the last 3 months.
    window: restrict training target months to the last `window` months.
    """
    site_level = level == "site"

    def predict(ctx):
        months, Y, N, units = panel(ctx, level)
        M, U = Y.shape
        if M < 15:
            return float(loc_damped(Y, M).sum())
        F, prow, z = _features(Y, N, months, site_level)
        lo = 13 if window is None else max(13, M - window)
        rows = np.arange(lo, M)
        X = np.stack([np.concatenate([F[k][r] for r in rows]) for k in FEATS], 1)
        yt = np.concatenate([z[r] for r in rows])
        w = np.concatenate([Y[r - 12] for r in rows])
        ok = np.isfinite(yt) & (w > 0)
        if site_level:
            ok &= np.concatenate([(Y[r] > 0) for r in rows])
        X, yt, w = X[ok], np.clip(yt[ok], -Z_CLIP, Z_CLIP), w[ok] / w[ok].mean()
        Xte = np.stack([prow[k] for k in FEATS], 1)
        zhat = np.clip(_fit_predict(kind, X, yt, w, Xte), -Z_CLIP, Z_CLIP)
        ly = Y[M - 12]
        recent = Y[M - 3:M].sum(0)
        if not churn:
            pred = ly * np.exp(zhat)
            pred = np.where(ly <= 0, recent / 3, pred)
            pred = np.where(recent <= 0, 0.0, pred)
            return float(pred.sum())
        # churn decomposition
        act = (ly > 0) & (recent > 0)
        G = (ly[act] * np.exp(zhat[act])).sum() / ly[act].sum()
        tot = Y.sum(1)
        cs = []
        for m in range(M - 3, M):
            mt = (Y[m] > 0) & (Y[m - 12] > 0)
            gm = Y[m][mt].sum() / Y[m - 12][mt].sum()
            cs.append(tot[m] / (tot[m - 12] * gm))
        return float(tot[M - 12] * G * np.mean(cs))
    predict.__name__ = f"global_{kind}_{level}" + (f"_w{window}" if window else "") + ("_churn" if churn else "")
    return predict


# --------------------------------------------------------------------------- ratio model (metric = visits x ratio)
def make_ratio_via_visits(level: str = "county"):
    """pounds / individuals forecast = bottom-up damped visits forecast x damped-YoY
    forecast of the statewide metric-per-visit ratio.  For visits it is the visits model."""
    bu = make_bottom_up(level, "damped50")

    def predict(ctx):
        months, V, _, _ = panel(ctx, level, "visits")
        i = len(V)
        vhat = loc_damped(V, i).sum()
        if ctx.metric == "visits":
            return float(vhat)
        _, Y, _, _ = panel(ctx, level, ctx.metric)
        v, y = V.sum(1), Y.sum(1)
        rho = y / v
        g = (y[i - 3:i].sum() / v[i - 3:i].sum()) / (y[i - 15:i - 12].sum() / v[i - 15:i - 12].sum())
        rhat = rho[i - 12] * (1 + DAMP * (g - 1))
        return float(vhat * rhat)
    predict.__name__ = f"ratio_via_visits_{level}"
    return predict


def make_mean(*fns, name="ens"):
    def predict(ctx):
        return float(np.mean([f(ctx) for f in fns]))
    predict.__name__ = name
    return predict
