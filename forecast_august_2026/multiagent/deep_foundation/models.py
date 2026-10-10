"""Deep-learning & foundation-model candidates for the multi-agent August study.

Every public model is ``predict(ctx) -> float`` (statewide total for ctx.metric,
ctx.target_month), using only ctx.y / ctx.monthly / ctx.site (all < target).

Families
--------
1. Zero-shot foundation models (Chronos-Bolt tiny/small/base, Chronos-2), median
   forecast, applied to the statewide series (raw or log) or to every county /
   food-bank series (summed).  Pretrained weights were released publicly by
   Amazon (amazon/chronos-bolt-* Nov 2024, amazon/chronos-2 Oct 2025) and were
   never trained on this private dataset -> no cutoff violation.
2. Global neural models (neuralforecast NHITS / NBEATS / MLP) trained on the
   county x metric panel (one model for all three metrics, per-window robust
   scaling), forecasts summed over counties.
   Retraining scheme (leakage-safe): retrain points R = {Jan, Apr, Jul, Oct} U {Aug}
   of every year.  For a target month t the model used is the one trained on
   data with month < c, where c = max{r in R : r <= t}.  Training data is
   ctx.site filtered to month < c (a subset of what is available at t); the
   up-to-date history (< t) is then fed as the input window.  So no model ever
   trains on data >= its forecast origin.  All August folds use a model trained
   exactly at the July 31 cutoff.
All hyperparameters fixed a priori; seeds fixed.
"""

from __future__ import annotations

import logging
import os
import warnings

import numpy as np
import pandas as pd
import torch

warnings.filterwarnings("ignore")
logging.getLogger("pytorch_lightning").setLevel(logging.ERROR)
logging.getLogger("lightning").setLevel(logging.ERROR)
logging.getLogger("lightning.pytorch").setLevel(logging.ERROR)
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
torch.set_num_threads(max(1, (os.cpu_count() or 2)))

METRICS = ("visits", "pounds", "individuals")
CHRONOS_IDS = {
    "bolt_tiny": "amazon/chronos-bolt-tiny",
    "bolt_small": "amazon/chronos-bolt-small",
    "bolt_base": "amazon/chronos-bolt-base",
    "chronos2": "amazon/chronos-2",
}
_PIPES: dict = {}


def _pipe(key):
    if key not in _PIPES:
        from chronos import BaseChronosPipeline
        torch.manual_seed(0)
        _PIPES[key] = BaseChronosPipeline.from_pretrained(CHRONOS_IDS[key], device_map="cpu",
                                                          torch_dtype=torch.float32)
    return _PIPES[key]


# ------------------------------------------------------------------ panels
def _norm_fb(s: pd.Series) -> pd.Series:
    return (s.str.replace("*", "", regex=False).str.replace(" Inc.", "", regex=False).str.strip())


def panel(site: pd.DataFrame, metric: str, key: str, end: pd.Timestamp) -> pd.DataFrame:
    """Wide matrix (series x months) of sums, months Jan 2022 .. end-1 month, NaN->0."""
    d = site[site["month"] < end].copy()
    if key == "food_bank":
        d["food_bank"] = _norm_fb(d["food_bank"])
    w = d.pivot_table(index=key, columns="month", values=metric, aggfunc="sum", fill_value=0.0)
    months = pd.date_range(d["month"].min(), end - pd.DateOffset(months=1), freq="MS")
    w = w.reindex(columns=months, fill_value=0.0).fillna(0.0)
    return w.loc[w.sum(axis=1) > 0]


# ------------------------------------------------------------------ chronos
def _median(key, series_list):
    """Median 1-step forecast for a list of 1-D numpy arrays."""
    p = _pipe(key)
    if key == "chronos2":
        q, _ = p.predict_quantiles([np.asarray(s, dtype=np.float32) for s in series_list],
                                   prediction_length=1, quantile_levels=[0.5])
        return np.array([float(x[0, 0, 0]) for x in q])
    ctx = [torch.tensor(np.asarray(s, dtype=np.float32)) for s in series_list]
    q, _ = p.predict_quantiles(ctx, prediction_length=1, quantile_levels=[0.5])
    return q[:, 0, 0].numpy().astype(float)


def chronos_state(key, log=False):
    def f(ctx):
        y = ctx.y.values.astype(float)
        if log:
            return float(np.exp(_median(key, [np.log(y)])[0]))
        return float(_median(key, [y])[0])
    return f


def chronos_panel(key, level):
    def f(ctx):
        w = panel(ctx.site, ctx.metric, level, ctx.target_month)
        preds = np.clip(_median(key, list(w.values)), 0, None)
        return float(preds.sum())
    return f


def chronos2_multivariate(ctx):
    """Chronos-2 with the three statewide metrics as jointly-modelled variates."""
    m = ctx.monthly.sort_values("month")
    X = np.log(m[list(METRICS)].values.T.astype(np.float32))  # (3, T)
    q, _ = _pipe("chronos2").predict_quantiles([X], prediction_length=1, quantile_levels=[0.5])
    return float(np.exp(q[0][METRICS.index(ctx.metric), 0, 0]))


def chronos2_panel_xlearn(level):
    """Chronos-2 on the panel with cross_learning (series attend to each other)."""
    def f(ctx):
        w = panel(ctx.site, ctx.metric, level, ctx.target_month)
        q, _ = _pipe("chronos2").predict_quantiles([v.astype(np.float32) for v in w.values],
                                                   prediction_length=1, quantile_levels=[0.5],
                                                   cross_learning=True)
        return float(np.clip([float(x[0, 0, 0]) for x in q], 0, None).sum())
    return f


# ------------------------------------------------------------------ neuralforecast
_NF_MODELS: dict = {}
_NF_PREDS: dict = {}


def retrain_cut(t: pd.Timestamp) -> pd.Timestamp:
    """Latest retrain point (1st of Jan/Apr/Jul/Aug/Oct) <= t."""
    c = t
    while c.month not in (1, 4, 7, 8, 10):
        c = c - pd.DateOffset(months=1)
    return c


def _long_panel(site, end):
    parts = []
    for m in METRICS:
        w = panel(site, m, "county", end)
        lg = w.stack().rename("y").reset_index()
        lg.columns = ["county", "ds", "y"]
        lg["unique_id"] = m + "|" + lg["county"].astype(str)
        parts.append(lg[["unique_id", "ds", "y"]])
    return pd.concat(parts, ignore_index=True)


def _build(name):
    from neuralforecast.models import MLP, NBEATS, NHITS
    common = dict(h=1, input_size=12, max_steps=300, learning_rate=1e-3, scaler_type="robust",
                  batch_size=64, windows_batch_size=256, random_seed=1, start_padding_enabled=True,
                  val_check_steps=1000, enable_progress_bar=False, enable_model_summary=False,
                  logger=False, accelerator="cpu", enable_checkpointing=False)
    if name == "nhits":
        return NHITS(**common)
    if name == "nbeats":
        return NBEATS(stack_types=["identity", "identity", "identity"], **common)  # generic N-BEATS (h=1)
    if name == "mlp":
        return MLP(num_layers=2, hidden_size=256, **common)
    raise ValueError(name)


def _nf_model(name, site, c):
    k = (name, c)
    if k not in _NF_MODELS:
        from neuralforecast import NeuralForecast
        torch.manual_seed(1)
        np.random.seed(1)
        nf = NeuralForecast(models=[_build(name)], freq="MS")
        nf.fit(df=_long_panel(site, c))       # data strictly < c <= target
        _NF_MODELS[k] = nf
    return _NF_MODELS[k]


def neural_county(name):
    def f(ctx):
        t = ctx.target_month
        k = (name, t)
        if k not in _NF_PREDS:
            c = retrain_cut(t)
            nf = _nf_model(name, ctx.site, c)
            hist = _long_panel(ctx.site, t)
            fc = nf.predict(df=hist)
            col = [x for x in fc.columns if x not in ("unique_id", "ds")][0]
            fc["metric"] = fc["unique_id"].str.split("|").str[0]
            fc["pred"] = fc[col].clip(lower=0)
            _NF_PREDS[k] = fc.groupby("metric")["pred"].sum().to_dict()
        return float(_NF_PREDS[k][ctx.metric])
    return f


# ------------------------------------------------------------------ registry
ZERO_SHOT = {
    "bolt_tiny_state": chronos_state("bolt_tiny"),
    "bolt_small_state": chronos_state("bolt_small"),
    "bolt_base_state": chronos_state("bolt_base"),
    "bolt_base_state_log": chronos_state("bolt_base", log=True),
    "bolt_base_foodbank": chronos_panel("bolt_base", "food_bank"),
    "bolt_base_county": chronos_panel("bolt_base", "county"),
    "chronos2_state": chronos_state("chronos2"),
    "chronos2_state_log": chronos_state("chronos2", log=True),
    "chronos2_multivar_log": chronos2_multivariate,
    "chronos2_foodbank": chronos_panel("chronos2", "food_bank"),
    "chronos2_county": chronos_panel("chronos2", "county"),
    "chronos2_county_xlearn": chronos2_panel_xlearn("county"),
}

NEURAL = {
    "nhits_county": neural_county("nhits"),
    "nbeats_county": neural_county("nbeats"),
    "mlp_county": neural_county("mlp"),
}
