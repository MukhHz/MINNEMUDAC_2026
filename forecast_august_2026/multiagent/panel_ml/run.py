"""Run all panel / many-model variants through the shared harness."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import harness  # noqa: E402
import models as M  # noqa: E402

np.random.seed(M.SEED)


def check_aggregation():
    """Units must sum to ctx.y for every level/metric (checked at a few cutoffs)."""
    lines = []
    for t in [pd.Timestamp("2023-08-01"), pd.Timestamp("2025-01-01"), harness.FINAL_TARGET]:
        for metric in harness.METRICS:
            ctx = harness.make_context(t, metric)
            for level in ("county", "food_bank", "site", "site_group"):
                months, Y, N, units = M.panel(ctx, level)
                diff = np.abs(Y.sum(1) - ctx.y.reindex(months).values).max()
                assert diff < 1e-6 * ctx.y.max(), (t, metric, level, diff)
                lines.append(f"PASS {t.date()} {metric:11s} {level:10s} units={len(units):4d} max|sum-ctx.y|={diff:.3g}")
    return lines


_RES_CACHE: dict = {}


def cached(name, fn):
    def predict(ctx):
        k = (name, ctx.target_month, ctx.metric)
        if k not in _RES_CACHE:
            _RES_CACHE[k] = fn(ctx)
        return _RES_CACHE[k]
    return predict


def build_models():
    m = {}
    # ---- local many-model, bottom-up
    for level in ("county", "food_bank", "site"):
        m[f"bu_damped50_{level}"] = M.make_bottom_up(level, "damped50")
        m[f"bu_yoyfull_{level}"] = M.make_bottom_up(level, "yoy_full")
        m[f"mmf_select_{level}"] = M.make_mmf_select(level)
        m[f"bu_damped_tuned_{level}"] = M.make_inner_tuned_damped(level)
    m["bu_seasonal_level_county"] = M.make_bottom_up("county", "seasonal_level")
    # ---- local ETS per unit
    m["ets_food_bank"] = M.make_ets("food_bank")
    m["ets_site_group"] = M.make_ets("site_group")
    # ---- global models on log-YoY ratio
    m["global_lgbm_county"] = M.make_global("county", "lgbm")
    m["global_ridge_county"] = M.make_global("county", "ridge")
    m["global_lgbm_county_w18"] = M.make_global("county", "lgbm", window=18)
    m["global_ridge_county_w18"] = M.make_global("county", "ridge", window=18)
    m["global_lgbm_site_churn"] = M.make_global("site", "lgbm", churn=True)
    m["global_ridge_site_churn"] = M.make_global("site", "ridge", churn=True)
    m["global_lgbm_food_bank"] = M.make_global("food_bank", "lgbm")  # few units: expected weak
    # ---- ratio
    m["ratio_via_visits_county"] = M.make_ratio_via_visits("county")
    m = {k: cached(k, v) for k, v in m.items()}
    # ---- a-priori ensemble
    m["ens_county_damped_lgbm_ridge"] = M.make_mean(m["bu_damped50_county"], m["global_lgbm_county"],
                                                    m["global_ridge_county"])
    m["ens_site_damped_lgbm"] = M.make_mean(m["bu_damped50_site"], m["global_lgbm_site_churn"])
    # reference baselines for side-by-side
    m.update(harness.BASELINES)
    return m


if __name__ == "__main__":
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    t0 = time.time()
    lines = check_aggregation()
    (out / "aggregation_check.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[-4:]))
    s = harness.evaluate(build_models(), out)
    pd.set_option("display.width", 250)
    cols = ["metric", "model", "aug_mape", "aug_2023", "aug_2024", "aug_2025", "aug_mape_2024_25",
            "monthly_mape", "monthly_median_ape", "forecast_aug_2026"]
    print(s[cols].round(4).to_string(index=False))
    pred = pd.read_csv(out / "predictions.csv")
    print("errors:", (pred.error.fillna("") != "").sum())
    print("seconds by model:\n", pred.groupby("model").seconds.sum().sort_values().to_string())
    print(f"total {time.time() - t0:.0f}s")
