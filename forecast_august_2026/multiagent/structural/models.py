"""Structural forecasting models for the multi-agent August study.

Every public model is ``predict(ctx) -> float`` (statewide total for ctx.metric
in ctx.target_month) and uses ONLY ctx.monthly / ctx.site, which the harness
has already truncated at the cutoff.  No external data, no randomness, no
tuning against harness scores: all choices are fixed a priori or chosen by
inner past-only rolling validation inside ctx.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

METRICS = ("visits", "pounds", "individuals")
Y1 = pd.DateOffset(years=1)
M1 = pd.DateOffset(months=1)


# ----------------------------------------------------------------- helpers
def norm_food_bank(s: pd.Series) -> pd.Series:
    """Collapse naming variants ('Channel One ...*', 'North Country ... Inc.')."""
    return (s.astype(str).str.replace("*", "", regex=False)
            .str.replace(r"\s+Inc\.?$", "", regex=True).str.strip())


def reporting(site: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Rows with a non-missing value for metric (a 'reporting' site-month)."""
    r = site[site[metric].notna()]
    return r[["site_id", "month", "food_bank", metric]].copy()


def wide(site: pd.DataFrame, metric: str) -> pd.DataFrame:
    """site x month matrix of metric (NaN = not reported)."""
    r = reporting(site, metric)
    return r.pivot_table(index="site_id", columns="month", values=metric, aggfunc="sum")


def window(t: pd.Timestamp, k: int) -> list[pd.Timestamp]:
    """The k months immediately before t."""
    return list(pd.date_range(t - pd.DateOffset(months=k), periods=k, freq="MS"))


def damped_yoy(y: pd.Series, t: pd.Timestamp, k: int = 3, d: float = 0.5) -> float:
    w = window(t, k)
    g = y.loc[w].sum() / y.loc[[x - Y1 for x in w]].sum()
    return float(y.loc[t - Y1] * (1 + d * (g - 1)))


def _has(y: pd.Series, months) -> bool:
    return all((m in y.index) and pd.notna(y.loc[m]) for m in months)


# ------------------------------------------------- 1. matched-panel growth
def matched_growth(W: pd.DataFrame, t: pd.Timestamp, k: int = 3) -> float:
    """Same-site growth over the last k months vs the same months a year ago,
    using only sites that reported in BOTH the month and its year-ago month."""
    num = den = 0.0
    for m in window(t, k):
        a, b = m, m - Y1
        if a not in W.columns or b not in W.columns:
            continue
        both = W[a].notna() & W[b].notna()
        num += W.loc[both, a].sum()
        den += W.loc[both, b].sum()
    return num / den if den > 0 else 1.0


def panel_growth(ctx, k: int = 3, d: float = 1.0, entry_exit: bool = True) -> float:
    """Last-year target total x matched same-site growth (damped by d),
    times an entry/exit composition factor = (total YoY in window) / (matched YoY)."""
    y, t = ctx.y, ctx.target_month
    W = wide(ctx.site, ctx.metric)
    g_same = matched_growth(W, t, k)
    comp = 1.0
    if entry_exit:
        w = window(t, k)
        g_tot = y.loc[w].sum() / y.loc[[x - Y1 for x in w]].sum()
        comp = g_tot / g_same
    g = g_same * comp
    return float(y.loc[t - Y1] * (1 + d * (g - 1)))


def panel_carry(ctx, k: int = 3, d: float = 0.5) -> float:
    """Site-set-aware panel model (explicit entry/exit adjustment).
    For each site s with a reporting weight p_s (p_stay if it reported in t-1,
    p_ret if it missed t-1 but reported t-2, else 0):
      - if s reported in the target month last year: y_s(LY) x damped same-site growth
      - else (entrant since LY):  recent level x pooled same-site seasonal ratio
    plus expected fresh-entrant mass (mean of last 12 months)."""
    t = ctx.target_month
    W = wide(ctx.site, ctx.metric)
    g = 1 + d * (matched_growth(W, t, k) - 1)
    last, prev, ly = t - M1, t - 2 * M1, t - Y1
    p_stay, p_ret = _return_prob(W, t)
    a1 = W[last].notna() if last in W.columns else pd.Series(False, index=W.index)
    a2 = W[prev].notna() if prev in W.columns else pd.Series(False, index=W.index)
    p = pd.Series(np.where(a1, p_stay, np.where(a2, p_ret, 0.0)), index=W.index)
    has_ly = W[ly].notna() if ly in W.columns else pd.Series(False, index=W.index)
    rec = W[[c for c in window(t, k) if c in W.columns]].mean(axis=1)
    season = _seasonal_site_ratio(W, t, k)
    part_ly = (p[has_ly] * W.loc[has_ly, ly]).sum() * g
    part_new = (p[~has_ly] * rec[~has_ly]).fillna(0).sum() * season
    cols = sorted(c for c in W.columns if c < t)
    masses = [W.loc[W[cols[i]].notna() & W[cols[i - 1]].isna() & W[cols[i - 2]].isna(), cols[i]].sum()
              for i in range(2, len(cols))]
    ent = float(np.mean(masses[-12:])) if masses else 0.0
    return float(part_ly + part_new + ent)


def panel_same_site_only(ctx):     # pure same-site growth, no composition, undamped
    return panel_growth(ctx, k=3, d=1.0, entry_exit=False)


def panel_same_site_damped(ctx):   # same-site growth, damped 0.5, no composition
    return panel_growth(ctx, k=3, d=0.5, entry_exit=False)


def panel_same_site_6m_damped(ctx):
    return panel_growth(ctx, k=6, d=0.5, entry_exit=False)


# ----------------------------------- 2. site-level expected-reporting build
def _seasonal_site_ratio(W: pd.DataFrame, t: pd.Timestamp, k: int = 3, years: int = 3) -> float:
    """Pooled matched-panel ratio target-month / mean(previous k months),
    averaged over up to `years` prior years (sites reporting in all k+1 months)."""
    rs = []
    for j in range(1, years + 1):
        tt = t - pd.DateOffset(years=j)
        w = window(tt, k)
        cols = w + [tt]
        if not all(c in W.columns for c in cols):
            continue
        sub = W[cols].dropna()
        if len(sub) < 30:
            continue
        rs.append(sub[tt].sum() / sub[w].mean(axis=1).sum())
    return float(np.mean(rs)) if rs else 1.0


def _return_prob(W: pd.DataFrame, t: pd.Timestamp, lookback: int = 12) -> tuple[float, float]:
    """Historical P(report in m | reported in m-1) and P(report in m | missed m-1
    but reported in m-2), estimated over the last `lookback` transitions < t."""
    cols = [c for c in W.columns if c < t]
    cols = sorted(cols)[-(lookback + 2):]
    stay = ret = n_stay = n_ret = 0
    for i in range(2, len(cols)):
        a, b, c = W[cols[i - 2]].notna(), W[cols[i - 1]].notna(), W[cols[i]].notna()
        stay += (b & c).sum(); n_stay += b.sum()
        ret += (a & ~b & c).sum(); n_ret += (a & ~b).sum()
    return (stay / n_stay if n_stay else 0.97), (ret / n_ret if n_ret else 0.5)


def site_build(ctx, k: int = 3, use_prob: bool = True, entrants: bool = True) -> float:
    """Sum over currently-active sites of P(report) x recent level x seasonal ratio,
    plus an expected-entrant term.

    level_s   = mean of site's reported values in the last k months
    season    = pooled same-site ratio target / mean(prev k) from prior years
    P(report) = historical continuation prob (reported t-1) or return prob
                (missed t-1, reported t-2)
    entrants  = mean over last 12 months of the mass of sites reporting in m that
                did not report in m-1 or m-2 (fresh/returning sites)
    """
    t = ctx.target_month
    W = wide(ctx.site, ctx.metric)
    w = window(t, k)
    rec = W[[c for c in w if c in W.columns]]
    level = rec.mean(axis=1, skipna=True)
    last, prev = t - M1, t - 2 * M1
    p_stay, p_ret = _return_prob(W, t)
    act_last = W[last].notna() if last in W.columns else pd.Series(False, index=W.index)
    act_prev = W[prev].notna() if prev in W.columns else pd.Series(False, index=W.index)
    if use_prob:
        p = np.where(act_last, p_stay, np.where(act_prev, p_ret, 0.0))
    else:
        p = np.where(act_last, 1.0, 0.0)
    season = _seasonal_site_ratio(W, t, k)
    total = float(np.nansum(level.values * p)) * season
    if entrants:
        cols = sorted(c for c in W.columns if c < t)
        masses = []
        for i in range(2, len(cols)):
            fresh = W[cols[i]].notna() & W[cols[i - 1]].isna() & W[cols[i - 2]].isna()
            masses.append(W.loc[fresh, cols[i]].sum())
        total += float(np.mean(masses[-12:])) if masses else 0.0
    return total


def site_build_prob(ctx):
    return site_build(ctx, k=3, use_prob=True, entrants=True)


def site_build_active_only(ctx):
    return site_build(ctx, k=3, use_prob=False, entrants=False)


# ------------------------------- 3. expected sites x per-site average
def sites_x_avg(ctx, d: float = 0.5, k: int = 3) -> float:
    """N_hat x avg_hat.
    N_hat   = mean number of reporting sites over last k months (sites are flat
              month to month; no seasonal pattern in counts).
    avg_hat = per-site average in target month last year x damped YoY growth
              of the per-site average over the last k months."""
    t, met = ctx.target_month, ctx.metric
    r = reporting(ctx.site, met)
    n = r.groupby("month").site_id.nunique()
    tot = r.groupby("month")[met].sum()
    avg = tot / n
    w = window(t, k)
    n_hat = n.loc[w].mean()
    g = avg.loc[w].mean() / avg.loc[[x - Y1 for x in w]].mean()
    a_hat = avg.loc[t - Y1] * (1 + d * (g - 1))
    return float(n_hat * a_hat)


def sites_x_avg_undamped(ctx):
    return sites_x_avg(ctx, d=1.0)


# ------------------------------------------- 4. cross-metric ratio models
def _ratio_forecast(ctx, base_fn, k: int = 3, seasonal: bool = True) -> float:
    """Forecast visits with base_fn, then metric = visits x recent ratio.
    Ratio = metric/visits over last k months, seasonally adjusted by
    (ratio in target-month last year / ratio in same k months last year)."""
    met = ctx.metric
    vctx = type(ctx)(ctx.target_month, "visits", ctx.monthly, ctx.site)
    v_hat = base_fn(vctx)
    if met == "visits":
        return float(v_hat)
    m = ctx.monthly.set_index("month").asfreq("MS")
    rat = m[met] / m["visits"]
    t = ctx.target_month
    w = window(t, k)
    r_now = m.loc[w, met].sum() / m.loc[w, "visits"].sum()
    if seasonal:
        wl = [x - Y1 for x in w]
        r_ly_w = m.loc[wl, met].sum() / m.loc[wl, "visits"].sum()
        r_now *= rat.loc[t - Y1] / r_ly_w
    return float(v_hat * r_now)


def xmetric_dyoy_seasonal(ctx):
    return _ratio_forecast(ctx, lambda c: damped_yoy(c.y, c.target_month, 3, 0.5), seasonal=True)


def xmetric_dyoy_flat(ctx):
    return _ratio_forecast(ctx, lambda c: damped_yoy(c.y, c.target_month, 3, 0.5), seasonal=False)


def xmetric_dyoy_12m_ratio(ctx):
    """Ratio from trailing 12 months (no seasonal adjustment needed: annual)."""
    return _ratio_forecast(ctx, lambda c: damped_yoy(c.y, c.target_month, 3, 0.5), k=12, seasonal=False)


# ---------------------------------------- 5. food-bank-level damped YoY
def foodbank_dyoy(ctx, k: int = 3, d: float = 0.5) -> float:
    """Damped YoY per (normalised) food bank, summed.  Food banks whose
    year-ago window is empty fall back to statewide growth."""
    t, met = ctx.target_month, ctx.metric
    s = ctx.site[ctx.site[met].notna()].copy()
    s["fb"] = norm_food_bank(s["food_bank"])
    P = s.pivot_table(index="month", columns="fb", values=met, aggfunc="sum").asfreq("MS").fillna(0.0)
    w = window(t, k)
    wl = [x - Y1 for x in w]
    g_state = ctx.y.loc[w].sum() / ctx.y.loc[wl].sum()
    total = 0.0
    for fb in P.columns:
        base = P.loc[t - Y1, fb] if (t - Y1) in P.index else 0.0
        den = P.loc[wl, fb].sum()
        g = P.loc[w, fb].sum() / den if den > 0 else g_state
        total += base * (1 + d * (g - 1))
    return float(total)


def foodbank_dyoy_6m(ctx):
    return foodbank_dyoy(ctx, k=6, d=0.5)


# --------------------------- 6. damped YoY with inner past-only selection
GRID_K = (1, 3, 6)
GRID_D = (0.0, 0.25, 0.5, 0.75, 1.0)


def _inner_errors(y: pd.Series, t: pd.Timestamp, n_origins: int = 12) -> pd.DataFrame:
    """APE of each (k, d) at the last n_origins one-step origins strictly < t
    (each inner origin uses only data before it)."""
    rows = []
    origins = [t - pd.DateOffset(months=i) for i in range(1, 60)]
    used = 0
    for o in origins:
        if used >= n_origins:
            break
        need = [x - Y1 for x in window(o, max(GRID_K))] + [o - Y1, o]
        if not _has(y, need):
            continue
        used += 1
        yy = y.loc[y.index < o]
        for k in GRID_K:
            for d in GRID_D:
                p = damped_yoy(yy, o, k, d)
                rows.append(dict(origin=o, k=k, d=d, ape=abs(p / y.loc[o] - 1)))
    return pd.DataFrame(rows)


def inner_dyoy(ctx, n_origins: int = 12, top: int = 1) -> float:
    y, t = ctx.y, ctx.target_month
    e = _inner_errors(y, t, n_origins)
    if e.empty:
        return damped_yoy(y, t, 3, 0.5)
    sc = e.groupby(["k", "d"]).ape.mean().sort_values()
    preds = [damped_yoy(y, t, k, d) for (k, d) in sc.index[:top]]
    return float(np.mean(preds))


def inner_dyoy_best(ctx):
    return inner_dyoy(ctx, 12, 1)


def inner_dyoy_top5(ctx):
    return inner_dyoy(ctx, 12, 5)


def inner_dyoy_24o_top5(ctx):
    return inner_dyoy(ctx, 24, 5)


# --------------------------------------------- 7. seasonal-ratio models
def seasonal_ratio(ctx, k: int = 1, years: int = 3) -> float:
    """Target = mean(last k months) x mean over prior years of
    target / mean(prev k months) (statewide)."""
    y, t = ctx.y, ctx.target_month
    w = window(t, k)
    rs = []
    for j in range(1, years + 1):
        tt = t - pd.DateOffset(years=j)
        ww = window(tt, k)
        if _has(y, ww + [tt]):
            rs.append(y.loc[tt] / y.loc[ww].mean())
    r = float(np.mean(rs)) if rs else 1.0
    return float(y.loc[w].mean() * r)


def ratio_last_month(ctx):
    return seasonal_ratio(ctx, k=1)


def ratio_last_3m(ctx):
    return seasonal_ratio(ctx, k=3)


# ------------------------------------------------ 8. simple combinations
def combo_dyoy_xmetric_fb(ctx):
    """Equal-weight mean of three structurally different damped-YoY views."""
    return float(np.mean([damped_yoy(ctx.y, ctx.target_month, 3, 0.5),
                          foodbank_dyoy(ctx), xmetric_dyoy_12m_ratio(ctx)]))


MODELS = {
    "panel_carry_d05": lambda c: panel_carry(c, 3, 0.5),
    "panel_carry_d1": lambda c: panel_carry(c, 3, 1.0),
    "panel_same_site_only": panel_same_site_only,
    "panel_same_site_damped": panel_same_site_damped,
    "panel_same_site_6m_damped": panel_same_site_6m_damped,
    "site_build_prob": site_build_prob,
    "site_build_active_only": site_build_active_only,
    "sites_x_avg_d05": sites_x_avg,
    "sites_x_avg_undamped": sites_x_avg_undamped,
    "xmetric_dyoy_seasonal": xmetric_dyoy_seasonal,
    "xmetric_dyoy_flat": xmetric_dyoy_flat,
    "xmetric_dyoy_12m_ratio": xmetric_dyoy_12m_ratio,
    "foodbank_dyoy_3m": foodbank_dyoy,
    "foodbank_dyoy_6m": foodbank_dyoy_6m,
    "inner_dyoy_best": inner_dyoy_best,
    "inner_dyoy_top5": inner_dyoy_top5,
    "inner_dyoy_24o_top5": inner_dyoy_24o_top5,
    "ratio_last_month": ratio_last_month,
    "ratio_last_3m": ratio_last_3m,
    "combo_dyoy_xmetric_fb": combo_dyoy_xmetric_fb,
}
