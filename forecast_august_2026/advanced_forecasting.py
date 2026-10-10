"""Leakage-safe advanced forecasts for Minnesota August 2026 food-shelf activity.

The script compares the locked statewide baselines with short-series statistical
models and global county-panel machine-learning models.  Every historical fold
uses only information available through July 31 of its forecast year.  The
August outcome is retrieved only after predictions have been generated.

Primary models use food-shelf history only.  A separately labelled LightGBM
sensitivity model adds SNAP variables whose exact publication dates have not
been verified; it is never eligible for primary model selection.
"""

from __future__ import annotations

import hashlib
import json
import platform
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import pandas as pd
import sklearn
import statsmodels
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX

try:
    from .forecast import METRICS, forecast_one_metric
except ImportError:  # Direct script execution.
    from forecast import METRICS, forecast_one_metric


RANDOM_SEED = 2026
BACKTEST_YEARS = (2023, 2024, 2025)
FINAL_YEAR = 2026
TARGET_VERSION = "reported"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
PIPELINE_DATA_DIR = PROJECT_DIR / "forecasting_pipeline" / "data"
OUTPUT_DIR = SCRIPT_DIR / "advanced_results"

COUNTY_FILE = PIPELINE_DATA_DIR / "food_county_month_clean.csv"
STATE_FILE = PIPELINE_DATA_DIR / "food_statewide_month_clean.csv"
SNAP_FILE = PIPELINE_DATA_DIR / "snap_state_month_clean.csv"
LOCKED_BASELINE_FILE = PROJECT_DIR / "Data" / "processed" / "foodshelf_site_month.csv"

LINEAR_MODELS = ("ridge_panel", "lasso_panel", "elastic_net_panel")
PANEL_MODELS = (*LINEAR_MODELS, "lightgbm_panel", "lightgbm_panel_snap_sensitivity")
PRIMARY_INELIGIBLE = {"lightgbm_panel_snap_sensitivity"}


@dataclass
class PanelFit:
    predictions: pd.DataFrame
    tuning: dict[str, Any]
    fitted_model: Pipeline
    numeric_features: list[str]
    categorical_features: list[str]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    county = pd.read_csv(COUNTY_FILE, dtype={"fips": "string"}, parse_dates=["date"])
    state = pd.read_csv(STATE_FILE, parse_dates=["date", "availability_date"])
    snap = pd.read_csv(SNAP_FILE, parse_dates=["date", "availability_date"])
    county["fips"] = county["fips"].str.zfill(5)

    assert county.duplicated(["fips", "date"]).sum() == 0
    assert state.duplicated(["date"]).sum() == 0
    assert state["date"].max() == pd.Timestamp("2026-07-01")
    assert not state["date"].eq(pd.Timestamp("2026-08-01")).any()
    assert county["fips"].nunique() == 87
    return county, state, snap


def _historical_seasonal_ratio(series: pd.Series, months: pd.Series) -> pd.Series:
    """Prior-years-only median ratio for the row's calendar month."""
    result = pd.Series(np.nan, index=series.index, dtype=float)
    history: dict[int, list[float]] = {month: [] for month in range(1, 13)}
    previous = np.nan
    for idx in series.index:
        month = int(months.loc[idx])
        if history[month]:
            result.loc[idx] = float(np.median(history[month]))
        current = series.loc[idx]
        if pd.notna(current) and pd.notna(previous) and float(previous) != 0:
            history[month].append(float(current) / float(previous))
        previous = current
    return result


def _snap_asof_features(target_dates: pd.Series, snap: pd.DataFrame) -> pd.DataFrame:
    snap = snap.sort_values("availability_date").reset_index(drop=True)
    value_by_date = snap.set_index("date")
    rows: list[dict[str, Any]] = []
    for target_date in sorted(pd.to_datetime(target_dates.unique())):
        cutoff = target_date - pd.Timedelta(days=1)
        available = snap.loc[snap["availability_date"].le(cutoff)]
        record: dict[str, Any] = {"date": target_date}
        if available.empty:
            for name in ("cases", "people", "expenditure", "people_per_case"):
                record[f"snap_{name}"] = np.nan
            for name in ("cases", "people", "expenditure"):
                record[f"snap_{name}_yoy"] = np.nan
            record["months_since_snap_observation"] = np.nan
        else:
            latest = available.iloc[-1]
            latest_date = pd.Timestamp(latest["date"])
            record["snap_cases"] = float(latest["snap_cases"])
            record["snap_people"] = float(latest["snap_people"])
            record["snap_expenditure"] = float(latest["snap_expenditure"])
            record["snap_people_per_case"] = (
                float(latest["snap_people"]) / float(latest["snap_cases"])
                if float(latest["snap_cases"]) != 0
                else np.nan
            )
            previous_date = latest_date - pd.DateOffset(years=1)
            if previous_date in value_by_date.index:
                previous = value_by_date.loc[previous_date]
                if isinstance(previous, pd.DataFrame):
                    previous = previous.iloc[-1]
                for source, short in (
                    ("snap_cases", "cases"),
                    ("snap_people", "people"),
                    ("snap_expenditure", "expenditure"),
                ):
                    denominator = float(previous[source])
                    record[f"snap_{short}_yoy"] = (
                        float(latest[source]) / denominator - 1 if denominator != 0 else np.nan
                    )
            else:
                for name in ("cases", "people", "expenditure"):
                    record[f"snap_{name}_yoy"] = np.nan
            record["months_since_snap_observation"] = (
                (target_date.year - latest_date.year) * 12
                + target_date.month
                - latest_date.month
            )
        rows.append(record)
    return pd.DataFrame(rows)


def build_panel_features(
    county: pd.DataFrame, snap: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    """Create prior-only county-panel features and append the August 2026 rows."""
    data = county.copy()
    target_columns = [f"{metric}_{TARGET_VERSION}" for metric in METRICS]

    eligible_fips = sorted(
        data.loc[~data["structural_missing_no_site"].astype(bool), "fips"].unique()
    )
    future = pd.DataFrame({"fips": eligible_fips, "date": pd.Timestamp("2026-08-01")})
    future["county"] = future["fips"].map(
        data.drop_duplicates("fips").set_index("fips")["county"]
    )
    for column in data.columns:
        if column not in future.columns:
            future[column] = np.nan
    future = future[data.columns]
    data = pd.concat([data, future], ignore_index=True)
    data = data.loc[data["fips"].isin(eligible_fips)].sort_values(["fips", "date"])
    data = data.reset_index(drop=True)

    data["year"] = data["date"].dt.year
    data["month_num"] = data["date"].dt.month
    data["month_cat"] = data["month_num"].astype(str)
    data["time_index"] = (
        (data["date"].dt.year - 2022) * 12 + data["date"].dt.month - 1
    ).astype(float)
    data["month_sin"] = np.sin(2 * np.pi * data["month_num"] / 12)
    data["month_cos"] = np.cos(2 * np.pi * data["month_num"] / 12)

    by_county = data.groupby("fips", sort=False)
    for source in target_columns:
        metric = source.removesuffix(f"_{TARGET_VERSION}")
        for lag in (1, 2, 3, 6, 12, 13):
            data[f"{metric}_lag_{lag}"] = by_county[source].shift(lag)
        for window in (3, 6, 12):
            data[f"{metric}_rolling_mean_{window}"] = by_county[source].transform(
                lambda values, w=window: values.shift(1).rolling(w, min_periods=max(2, w // 2)).mean()
            )
            data[f"{metric}_rolling_median_{window}"] = by_county[source].transform(
                lambda values, w=window: values.shift(1).rolling(w, min_periods=max(2, w // 2)).median()
            )
        data[f"{metric}_yoy_growth"] = (
            data[f"{metric}_lag_1"] / data[f"{metric}_lag_13"] - 1
        )

        ytd_prior = data.groupby(["fips", "year"], sort=False)[source].transform(
            lambda values: values.fillna(0).cumsum().shift(1)
        )
        data[f"{metric}_ytd_prior"] = ytd_prior
        cumulative = data.groupby(["fips", "year"], sort=False)[source].transform(
            lambda values: values.fillna(0).cumsum()
        )
        ytd_lookup = {
            (fips, int(year), int(month)): float(value)
            for fips, year, month, value in zip(
                data["fips"], data["year"], data["month_num"], cumulative
            )
            if pd.notna(value)
        }
        previous_ytd = []
        for row in data[["fips", "year", "month_num"]].itertuples(index=False):
            lookup_month = int(row.month_num) - 1
            previous_ytd.append(
                ytd_lookup.get((row.fips, int(row.year) - 1, lookup_month), np.nan)
                if lookup_month >= 1
                else np.nan
            )
        data[f"{metric}_previous_ytd"] = previous_ytd
        data[f"{metric}_ytd_growth"] = (
            data[f"{metric}_ytd_prior"] / data[f"{metric}_previous_ytd"] - 1
        )

        ratio_parts = []
        for _, group in data.groupby("fips", sort=False):
            ratio_parts.append(
                _historical_seasonal_ratio(group[source], group["month_num"])
            )
        data[f"{metric}_historical_month_ratio"] = pd.concat(ratio_parts).sort_index()

        state_totals = data.groupby("date")[source].sum(min_count=1)
        previous_dates = data["date"] - pd.DateOffset(months=1)
        previous_state_total = previous_dates.map(state_totals)
        data[f"{metric}_state_share_lag_1"] = (
            data[f"{metric}_lag_1"] / previous_state_total.to_numpy()
        )

    for coverage in ("n_sites", "n_sites_reported", "n_sites_missing"):
        data[f"{coverage}_lag_1"] = by_county[coverage].shift(1)
        data[f"{coverage}_lag_12"] = by_county[coverage].shift(12)
    data["reporting_rate_lag_1"] = data["n_sites_reported_lag_1"] / data["n_sites_lag_1"]

    data["pounds_per_visit_lag_1"] = data["pounds_lag_1"] / data["visits_lag_1"]
    data["individuals_per_visit_lag_1"] = (
        data["individuals_lag_1"] / data["visits_lag_1"]
    )

    snap_features = _snap_asof_features(data["date"], snap)
    data = data.merge(snap_features, on="date", how="left", validate="many_to_one")
    numeric_columns = data.select_dtypes(include=[np.number]).columns
    data[numeric_columns] = data[numeric_columns].replace([np.inf, -np.inf], np.nan)
    return data, eligible_fips


def feature_lists(metric: str, *, include_snap: bool) -> tuple[list[str], list[str]]:
    own = [
        *[f"{metric}_lag_{lag}" for lag in (1, 2, 3, 6, 12)],
        *[f"{metric}_rolling_mean_{window}" for window in (3, 6, 12)],
        f"{metric}_rolling_median_3",
        f"{metric}_yoy_growth",
        f"{metric}_ytd_growth",
        f"{metric}_historical_month_ratio",
        f"{metric}_state_share_lag_1",
    ]
    cross = []
    for other in METRICS:
        if other != metric:
            cross.extend([f"{other}_lag_1", f"{other}_lag_12"])
    numeric = [
        *own,
        *cross,
        "n_sites_lag_1",
        "n_sites_reported_lag_1",
        "n_sites_missing_lag_1",
        "reporting_rate_lag_1",
        "pounds_per_visit_lag_1",
        "individuals_per_visit_lag_1",
        "time_index",
        "month_sin",
        "month_cos",
    ]
    if include_snap:
        numeric.extend(
            [
                "snap_cases",
                "snap_people",
                "snap_expenditure",
                "snap_people_per_case",
                "snap_cases_yoy",
                "snap_people_yoy",
                "snap_expenditure_yoy",
                "months_since_snap_observation",
            ]
        )
    return numeric, ["fips", "month_cat"]


def make_preprocessor(
    numeric_features: list[str], categorical_features: list[str], *, scale: bool
) -> ColumnTransformer:
    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median", keep_empty_features=True))
    ]
    if scale:
        numeric_steps.append(("scaler", StandardScaler()))
    return ColumnTransformer(
        [
            ("numeric", Pipeline(numeric_steps), numeric_features),
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=True),
                categorical_features,
            ),
        ],
        remainder="drop",
    )


def estimator_for(model_name: str, params: dict[str, Any]) -> Any:
    if model_name == "ridge_panel":
        return Ridge(alpha=float(params["alpha"]))
    if model_name == "lasso_panel":
        return Lasso(alpha=float(params["alpha"]), max_iter=25_000, selection="cyclic")
    if model_name == "elastic_net_panel":
        return ElasticNet(
            alpha=float(params["alpha"]),
            l1_ratio=float(params["l1_ratio"]),
            max_iter=25_000,
            selection="cyclic",
        )
    if model_name.startswith("lightgbm_panel"):
        return lgb.LGBMRegressor(
            objective="regression_l1",
            n_estimators=250,
            learning_rate=0.025,
            num_leaves=15,
            max_depth=4,
            min_child_samples=60,
            subsample=0.85,
            colsample_bytree=0.80,
            reg_alpha=1.0,
            reg_lambda=8.0,
            random_state=RANDOM_SEED,
            n_jobs=1,
            deterministic=True,
            force_col_wise=True,
            verbosity=-1,
        )
    raise KeyError(model_name)


def parameter_grid(model_name: str) -> list[dict[str, Any]]:
    if model_name == "ridge_panel":
        return [{"alpha": value} for value in (0.1, 1.0, 10.0, 100.0)]
    if model_name == "lasso_panel":
        return [{"alpha": value} for value in (0.001, 0.005, 0.01, 0.05)]
    if model_name == "elastic_net_panel":
        return [
            {"alpha": alpha, "l1_ratio": ratio}
            for alpha in (0.001, 0.01, 0.05)
            for ratio in (0.2, 0.5, 0.8)
        ]
    return [{}]


def make_panel_pipeline(
    model_name: str,
    params: dict[str, Any],
    numeric_features: list[str],
    categorical_features: list[str],
) -> Pipeline:
    scale = model_name in LINEAR_MODELS
    return Pipeline(
        [
            (
                "preprocess",
                make_preprocessor(numeric_features, categorical_features, scale=scale),
            ),
            ("model", estimator_for(model_name, params)),
        ]
    )


def tune_panel_model(
    model_name: str,
    train: pd.DataFrame,
    target_column: str,
    numeric_features: list[str],
    categorical_features: list[str],
) -> dict[str, Any]:
    grid = parameter_grid(model_name)
    if len(grid) == 1:
        return grid[0]

    dates = sorted(train["date"].unique())
    validation_dates = dates[-4:]
    best_params = grid[0]
    best_wape = np.inf
    for params in grid:
        absolute_error = 0.0
        absolute_actual = 0.0
        successful_folds = 0
        for validation_date in validation_dates:
            inner_train = train.loc[train["date"].lt(validation_date)]
            inner_valid = train.loc[train["date"].eq(validation_date)]
            if inner_train["date"].nunique() < 6 or inner_valid.empty:
                continue
            pipeline = make_panel_pipeline(
                model_name, params, numeric_features, categorical_features
            )
            x_train = inner_train[numeric_features + categorical_features]
            y_train = np.log1p(inner_train[target_column].clip(lower=0))
            pipeline.fit(x_train, y_train)
            prediction = np.expm1(
                pipeline.predict(inner_valid[numeric_features + categorical_features])
            ).clip(min=0)
            actual = inner_valid[target_column].to_numpy(dtype=float)
            absolute_error += float(np.abs(prediction - actual).sum())
            absolute_actual += float(np.abs(actual).sum())
            successful_folds += 1
        if successful_folds and absolute_actual > 0:
            score = absolute_error / absolute_actual
            if score < best_wape:
                best_wape = score
                best_params = params
    return {**best_params, "inner_wape": None if not np.isfinite(best_wape) else best_wape}


def fit_panel_model(
    panel: pd.DataFrame,
    model_name: str,
    metric: str,
    cutoff: pd.Timestamp,
    target_date: pd.Timestamp,
) -> PanelFit:
    include_snap = model_name.endswith("snap_sensitivity")
    numeric_features, categorical_features = feature_lists(metric, include_snap=include_snap)
    target_column = f"{metric}_{TARGET_VERSION}"
    train = panel.loc[
        panel["date"].le(cutoff)
        & panel[target_column].notna()
        & panel[f"{metric}_lag_1"].notna()
    ].copy()
    predict = panel.loc[panel["date"].eq(target_date)].copy()
    assert not train["date"].gt(cutoff).any()
    assert not train["date"].eq(target_date).any()
    if predict.empty:
        raise ValueError(f"No panel rows for {target_date:%Y-%m}")

    tuned = tune_panel_model(
        model_name,
        train,
        target_column,
        numeric_features,
        categorical_features,
    )
    fit_params = {key: value for key, value in tuned.items() if key != "inner_wape"}
    pipeline = make_panel_pipeline(
        model_name, fit_params, numeric_features, categorical_features
    )
    pipeline.fit(
        train[numeric_features + categorical_features],
        np.log1p(train[target_column].clip(lower=0)),
    )
    predicted = np.expm1(
        pipeline.predict(predict[numeric_features + categorical_features])
    ).clip(min=0)
    predictions = predict[["fips", "county", "date"]].copy()
    predictions["prediction"] = predicted
    return PanelFit(
        predictions=predictions,
        tuning=tuned,
        fitted_model=pipeline,
        numeric_features=numeric_features,
        categorical_features=categorical_features,
    )


def ets_forecast(train: pd.DataFrame, metric: str) -> tuple[float, str]:
    values = train.set_index("date")[metric].astype(float).asfreq("MS")
    candidates: list[tuple[str, dict[str, Any]]] = [
        ("holt_damped", {"trend": "add", "damped_trend": True, "seasonal": None}),
        ("level_only", {"trend": None, "seasonal": None}),
    ]
    if len(values) >= 24:
        candidates.extend(
            [
                (
                    "additive_damped",
                    {
                        "trend": "add",
                        "damped_trend": True,
                        "seasonal": "add",
                        "seasonal_periods": 12,
                    },
                ),
                (
                    "additive_seasonal",
                    {"trend": None, "seasonal": "add", "seasonal_periods": 12},
                ),
            ]
        )
    fits = []
    for label, config in candidates:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = ExponentialSmoothing(
                    values, initialization_method="estimated", **config
                ).fit(optimized=True, use_brute=False)
            fits.append((float(fit.aic), label, max(0.0, float(fit.forecast(1).iloc[0]))))
        except Exception:
            continue
    if not fits:
        return float(values.iloc[-1]), "fallback_last_value"
    _, label, prediction = min(fits, key=lambda item: item[0])
    return prediction, label


def sarima_forecast(train: pd.DataFrame, metric: str) -> tuple[float, str]:
    values = train.set_index("date")[metric].astype(float).asfreq("MS")
    candidates = [
        ((0, 1, 1), (0, 1, 1, 12)),
        ((1, 0, 0), (1, 0, 0, 12)),
        ((1, 1, 0), (0, 1, 1, 12)),
    ]
    fits = []
    for order, seasonal_order in candidates:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                fit = SARIMAX(
                    values,
                    order=order,
                    seasonal_order=seasonal_order,
                    trend="c" if order[1] == 0 else "n",
                    enforce_stationarity=False,
                    enforce_invertibility=False,
                ).fit(disp=False, maxiter=300)
            prediction = max(0.0, float(fit.forecast(1).iloc[0]))
            fits.append((float(fit.aic), order, seasonal_order, prediction))
        except Exception:
            continue
    if not fits:
        return float(values.iloc[-1]), "fallback_last_value"
    _, order, seasonal_order, prediction = min(fits, key=lambda item: item[0])
    return prediction, f"SARIMA{order}x{seasonal_order}"


def structural_predictions(
    county: pd.DataFrame,
    visits_predictions: pd.DataFrame,
    metric: str,
    cutoff: pd.Timestamp,
) -> pd.DataFrame:
    if metric not in {"pounds", "individuals"}:
        raise ValueError(metric)
    history = county.loc[
        county["date"].le(cutoff) & ~county["structural_missing_no_site"].astype(bool)
    ].copy()
    numerator = f"{metric}_{TARGET_VERSION}"
    denominator = f"visits_{TARGET_VERSION}"
    history["ratio"] = history[numerator] / history[denominator].replace(0, np.nan)
    august_ratio = (
        history.loc[history["date"].dt.month.eq(8)]
        .groupby("fips")["ratio"]
        .median()
    )
    recent_ratio = history.groupby("fips")["ratio"].apply(lambda values: values.tail(12).median())
    fallback = float(history["ratio"].median())
    output = visits_predictions.copy()
    output["ratio"] = output["fips"].map(august_ratio)
    output["ratio"] = output["ratio"].fillna(output["fips"].map(recent_ratio)).fillna(fallback)
    output["prediction"] = (output["prediction"] * output["ratio"]).clip(lower=0)
    return output.drop(columns="ratio")


def actual_county_values(
    county: pd.DataFrame, metric: str, target_date: pd.Timestamp
) -> pd.DataFrame:
    target = f"{metric}_{TARGET_VERSION}"
    actual = county.loc[
        county["date"].eq(target_date) & ~county["structural_missing_no_site"].astype(bool),
        ["fips", target],
    ].rename(columns={target: "actual"})
    return actual


def add_state_record(
    records: list[dict[str, Any]],
    *,
    year: int,
    metric: str,
    model: str,
    actual: float | None,
    prediction: float,
    detail: str = "",
) -> None:
    record = {
        "forecast_year": year,
        "cutoff": f"{year}-07-31",
        "target_month": f"{year}-08-01",
        "metric": metric,
        "model": model,
        "prediction": float(prediction),
        "eligible_for_primary": model not in PRIMARY_INELIGIBLE,
        "model_detail": detail,
    }
    if actual is not None:
        error = float(prediction) - float(actual)
        record.update(
            {
                "actual": float(actual),
                "error": error,
                "absolute_error": abs(error),
                "absolute_percentage_error": abs(error) / float(actual),
            }
        )
    records.append(record)


def run_fold(
    year: int,
    county: pd.DataFrame,
    state: pd.DataFrame,
    panel: pd.DataFrame,
    *,
    final: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, PanelFit]]:
    cutoff = pd.Timestamp(year, 7, 31)
    target_date = pd.Timestamp(year, 8, 1)
    state_train = state.loc[state["date"].le(cutoff)].copy()
    state_train = state_train.rename(
        columns={f"{metric}_{TARGET_VERSION}": metric for metric in METRICS}
    )
    state_train["year"] = state_train["date"].dt.year
    state_train["month_num"] = state_train["date"].dt.month
    state_train["month"] = state_train["date"]
    assert state_train["date"].max() == pd.Timestamp(year, 7, 1)

    state_records: list[dict[str, Any]] = []
    county_records: list[dict[str, Any]] = []
    tuning_records: list[dict[str, Any]] = []
    fitted: dict[str, PanelFit] = {}
    actual_state_row = state.loc[state["date"].eq(target_date)]

    panel_predictions: dict[tuple[str, str], pd.DataFrame] = {}
    for metric in METRICS:
        actual_state = None if final else float(actual_state_row.iloc[0][f"{metric}_{TARGET_VERSION}"])
        baseline_predictions = forecast_one_metric(state_train, metric, year)
        for model, prediction in baseline_predictions.items():
            add_state_record(
                state_records,
                year=year,
                metric=metric,
                model=model,
                actual=actual_state,
                prediction=prediction,
            )

        ets_prediction, ets_detail = ets_forecast(state_train, metric)
        add_state_record(
            state_records,
            year=year,
            metric=metric,
            model="ets",
            actual=actual_state,
            prediction=ets_prediction,
            detail=ets_detail,
        )
        sarima_prediction, sarima_detail = sarima_forecast(state_train, metric)
        add_state_record(
            state_records,
            year=year,
            metric=metric,
            model="sarima",
            actual=actual_state,
            prediction=sarima_prediction,
            detail=sarima_detail,
        )

        actual_counties = None if final else actual_county_values(county, metric, target_date)
        for model in PANEL_MODELS:
            fit = fit_panel_model(panel, model, metric, cutoff, target_date)
            fitted[f"{metric}:{model}"] = fit
            panel_predictions[(metric, model)] = fit.predictions
            prediction = float(fit.predictions["prediction"].sum())
            add_state_record(
                state_records,
                year=year,
                metric=metric,
                model=model,
                actual=actual_state,
                prediction=prediction,
                detail=json.dumps(fit.tuning, sort_keys=True),
            )
            tuning_records.append(
                {
                    "forecast_year": year,
                    "metric": metric,
                    "model": model,
                    **fit.tuning,
                }
            )
            if not final and actual_counties is not None:
                scored = fit.predictions.merge(actual_counties, on="fips", how="inner")
                scored = scored.dropna(subset=["actual"])
                for row in scored.itertuples(index=False):
                    county_records.append(
                        {
                            "forecast_year": year,
                            "metric": metric,
                            "model": model,
                            "fips": row.fips,
                            "actual": float(row.actual),
                            "prediction": float(row.prediction),
                        }
                    )

    for metric in ("pounds", "individuals"):
        visits = panel_predictions[("visits", "elastic_net_panel")]
        structural = structural_predictions(county, visits, metric, cutoff)
        panel_predictions[(metric, "structural_elastic_visits_x_ratio")] = structural
        actual_state = (
            None if final else float(actual_state_row.iloc[0][f"{metric}_{TARGET_VERSION}"])
        )
        add_state_record(
            state_records,
            year=year,
            metric=metric,
            model="structural_elastic_visits_x_ratio",
            actual=actual_state,
            prediction=float(structural["prediction"].sum()),
        )
        if not final:
            scored = structural.merge(
                actual_county_values(county, metric, target_date), on="fips", how="inner"
            ).dropna(subset=["actual"])
            for row in scored.itertuples(index=False):
                county_records.append(
                    {
                        "forecast_year": year,
                        "metric": metric,
                        "model": "structural_elastic_visits_x_ratio",
                        "fips": row.fips,
                        "actual": float(row.actual),
                        "prediction": float(row.prediction),
                    }
                )

    frame = pd.DataFrame(state_records)
    for metric in METRICS:
        component_names = ["seasonal_naive", "ets", "elastic_net_panel", "lightgbm_panel"]
        values = frame.loc[
            frame["metric"].eq(metric) & frame["model"].isin(component_names), "prediction"
        ]
        actual_state = (
            None if final else float(actual_state_row.iloc[0][f"{metric}_{TARGET_VERSION}"])
        )
        add_state_record(
            state_records,
            year=year,
            metric=metric,
            model="core_median_ensemble",
            actual=actual_state,
            prediction=float(values.median()),
            detail="median(seasonal_naive, ets, elastic_net_panel, lightgbm_panel)",
        )
    return state_records, county_records, tuning_records, fitted


def statewide_summary(backtests: pd.DataFrame) -> pd.DataFrame:
    naive = backtests.loc[backtests["model"].eq("seasonal_naive")].set_index(
        ["metric", "forecast_year"]
    )["absolute_percentage_error"]
    rows = []
    for (metric, model), group in backtests.groupby(["metric", "model"], sort=False):
        rows.append(
            {
                "metric": metric,
                "model": model,
                "folds": len(group),
                "mape": float(group["absolute_percentage_error"].mean()),
                "median_ape": float(group["absolute_percentage_error"].median()),
                "mae": float(group["absolute_error"].mean()),
                "rmse": float(np.sqrt(np.mean(np.square(group["error"])))),
                "wape": float(group["absolute_error"].sum() / group["actual"].abs().sum()),
                "folds_better_than_naive": int(
                    sum(
                        row.absolute_percentage_error
                        < naive.loc[(metric, row.forecast_year)]
                        for row in group.itertuples()
                    )
                ),
                "eligible_for_primary": bool(group["eligible_for_primary"].all()),
            }
        )
    return pd.DataFrame(rows).sort_values(["metric", "mape", "model"]).reset_index(drop=True)


def county_summary(predictions: pd.DataFrame) -> pd.DataFrame:
    predictions = predictions.copy()
    predictions["error"] = predictions["prediction"] - predictions["actual"]
    predictions["absolute_error"] = predictions["error"].abs()
    denominator = (predictions["actual"].abs() + predictions["prediction"].abs()) / 2
    predictions["smape_component"] = predictions["absolute_error"] / denominator.replace(0, np.nan)
    predictions["ape"] = predictions["absolute_error"] / predictions["actual"].abs().replace(0, np.nan)
    rows = []
    for (metric, model), group in predictions.groupby(["metric", "model"], sort=False):
        rows.append(
            {
                "metric": metric,
                "model": model,
                "county_predictions": len(group),
                "wape": float(group["absolute_error"].sum() / group["actual"].abs().sum()),
                "mae": float(group["absolute_error"].mean()),
                "rmse": float(np.sqrt(np.mean(np.square(group["error"])))),
                "smape": float(group["smape_component"].mean(skipna=True)),
                "median_ape": float(group["ape"].median(skipna=True)),
            }
        )
    return pd.DataFrame(rows).sort_values(["metric", "wape", "model"]).reset_index(drop=True)


def select_models(summary: pd.DataFrame) -> dict[str, str]:
    selected: dict[str, str] = {}
    for metric in METRICS:
        rows = summary.loc[summary["metric"].eq(metric)].copy()
        naive_mape = float(rows.loc[rows["model"].eq("seasonal_naive"), "mape"].iloc[0])
        eligible = rows.loc[
            rows["eligible_for_primary"]
            & rows["folds"].eq(len(BACKTEST_YEARS))
            & rows["mape"].lt(naive_mape)
            & rows["folds_better_than_naive"].eq(len(BACKTEST_YEARS))
        ]
        selected[metric] = (
            str(eligible.sort_values("mape").iloc[0]["model"])
            if not eligible.empty
            else "seasonal_naive"
        )
    return selected


def coefficient_table(fitted: dict[str, PanelFit]) -> pd.DataFrame:
    rows = []
    for key, fit in fitted.items():
        metric, model_name = key.split(":", 1)
        if model_name not in LINEAR_MODELS:
            continue
        model = fit.fitted_model.named_steps["model"]
        names = fit.fitted_model.named_steps["preprocess"].get_feature_names_out()
        coefficients = np.asarray(model.coef_).ravel()
        for name, coefficient in zip(names, coefficients):
            rows.append(
                {
                    "metric": metric,
                    "model": model_name,
                    "feature": name,
                    "coefficient": float(coefficient),
                    "absolute_coefficient": abs(float(coefficient)),
                    "selected_nonzero": abs(float(coefficient)) > 1e-8,
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["metric", "model", "absolute_coefficient"], ascending=[True, True, False]
    )


def lightgbm_importance_table(fitted: dict[str, PanelFit]) -> pd.DataFrame:
    rows = []
    for key, fit in fitted.items():
        metric, model_name = key.split(":", 1)
        if not model_name.startswith("lightgbm_panel"):
            continue
        model = fit.fitted_model.named_steps["model"]
        names = fit.fitted_model.named_steps["preprocess"].get_feature_names_out()
        importances = np.asarray(model.feature_importances_).ravel()
        for name, importance in zip(names, importances):
            rows.append(
                {
                    "metric": metric,
                    "model": model_name,
                    "feature": name,
                    "split_importance": int(importance),
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["metric", "model", "split_importance"], ascending=[True, True, False]
    )


def source_scope_audit(state: pd.DataFrame) -> pd.DataFrame:
    """Document why the advanced clean series differs from the locked raw baseline."""
    baseline = pd.read_csv(LOCKED_BASELINE_FILE, parse_dates=["month"])
    baseline_monthly = (
        baseline.groupby("month", as_index=False)[list(METRICS)].sum(min_count=1)
    )
    clean = state[["date", *[f"{metric}_{TARGET_VERSION}" for metric in METRICS]]].copy()
    audit = baseline_monthly.merge(clean, left_on="month", right_on="date", validate="one_to_one")
    for metric in METRICS:
        audit[f"clean_minus_locked_{metric}"] = (
            audit[f"{metric}_{TARGET_VERSION}"] - audit[metric]
        )
    audit["locked_baseline_rows"] = len(baseline)
    audit["advanced_clean_rows"] = len(pd.read_csv(PIPELINE_DATA_DIR / "food_site_month_clean.csv"))
    audit["rows_excluded_as_meal_programs"] = int(
        baseline.get("site_group", pd.Series(dtype="object")).eq("meal").sum()
    )
    audit["scope_note"] = (
        "Advanced models use the forecasting_pipeline clean export, which excludes meal-program rows; "
        "the earlier locked baseline source includes them."
    )
    return audit


def write_results_markdown(
    summary: pd.DataFrame, final: pd.DataFrame, selected: dict[str, str]
) -> None:
    lines = [
        "# Advanced August 2026 forecasting results",
        "",
        "## Selection policy",
        "",
        "The primary model remains seasonal naive unless a challenger has lower mean MAPE and beats it in all three August folds. SNAP sensitivity models are never eligible for primary selection because exact release dates are unverified.",
        "",
        "## Statewide rolling-August comparison",
        "",
        summary.assign(
            mape=lambda x: (100 * x["mape"]).round(2),
            wape=lambda x: (100 * x["wape"]).round(2),
            median_ape=lambda x: (100 * x["median_ape"]).round(2),
        )[
            [
                "metric",
                "model",
                "mape",
                "median_ape",
                "wape",
                "mae",
                "rmse",
                "folds_better_than_naive",
                "eligible_for_primary",
            ]
        ].to_markdown(index=False),
        "",
        "## August 2026 forecasts",
        "",
        final[["metric", "model", "forecast", "selected", "eligible_for_primary"]].to_markdown(index=False),
        "",
        "## Selected hold forecast",
        "",
    ]
    for metric, model in selected.items():
        value = float(
            final.loc[final["metric"].eq(metric) & final["model"].eq(model), "forecast"].iloc[0]
        )
        lines.append(f"- {metric}: {value:,.2f} using `{model}`")
    lines.extend(
        [
            "",
            "## Important limitations",
            "",
            "- Only three historical August holdouts are available, so rankings are uncertain.",
            "- County-panel models share information across counties but do not create additional years of statewide history.",
            "- This experiment uses the newer clean export that excludes meal-program rows; do not mix its forecasts or metrics with the earlier locked baseline source that includes 2,702 meal rows.",
            "- Reported outcomes are primary; site-imputed outcomes remain sensitivity data because masked-value validation error was high.",
            "- Poverty and MMG variables are excluded from the primary experiment because their conservative availability rules do not provide a consistent feature history for the August 2023 fold.",
            "- Deep learning is not included: four annual cycles are insufficient to justify it as a primary challenger.",
            "",
        ]
    )
    (OUTPUT_DIR / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    county, state, snap = load_inputs()
    panel, eligible_fips = build_panel_features(county, snap)

    state_rows: list[dict[str, Any]] = []
    county_rows: list[dict[str, Any]] = []
    tuning_rows: list[dict[str, Any]] = []
    for year in BACKTEST_YEARS:
        fold_state, fold_county, fold_tuning, _ = run_fold(
            year, county, state, panel, final=False
        )
        state_rows.extend(fold_state)
        county_rows.extend(fold_county)
        tuning_rows.extend(fold_tuning)

    backtests = pd.DataFrame(state_rows)
    county_backtests = pd.DataFrame(county_rows)
    summary = statewide_summary(backtests)
    county_metrics = county_summary(county_backtests)
    selected = select_models(summary)

    final_rows, _, final_tuning, final_fitted = run_fold(
        FINAL_YEAR, county, state, panel, final=True
    )
    tuning_rows.extend(final_tuning)
    final = pd.DataFrame(final_rows).rename(columns={"prediction": "forecast"})
    final["selected"] = final.apply(
        lambda row: row["model"] == selected[row["metric"]], axis=1
    )

    backtests.to_csv(OUTPUT_DIR / "statewide_backtest_predictions.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "statewide_model_summary.csv", index=False)
    county_backtests.to_csv(OUTPUT_DIR / "county_backtest_predictions.csv", index=False)
    county_metrics.to_csv(OUTPUT_DIR / "county_model_summary.csv", index=False)
    final.to_csv(OUTPUT_DIR / "final_forecasts_all_models.csv", index=False)
    final.loc[final["selected"]].to_csv(OUTPUT_DIR / "selected_forecasts.csv", index=False)
    pd.DataFrame(tuning_rows).to_csv(OUTPUT_DIR / "tuning_history.csv", index=False)
    coefficient_table(final_fitted).to_csv(
        OUTPUT_DIR / "regularized_coefficients.csv", index=False
    )
    lightgbm_importance_table(final_fitted).to_csv(
        OUTPUT_DIR / "lightgbm_feature_importance.csv", index=False
    )
    source_scope_audit(state).to_csv(OUTPUT_DIR / "source_scope_audit.csv", index=False)

    feature_audit = pd.DataFrame(
        [
            {
                "feature_group": "food-shelf lag and rolling features",
                "status": "primary",
                "reason": "Computed with shift(1) or earlier within each cutoff.",
            },
            {
                "feature_group": "county and calendar month",
                "status": "primary",
                "reason": "Known before the forecast month.",
            },
            {
                "feature_group": "lagged reporting-site coverage",
                "status": "primary",
                "reason": "Only prior-month counts are used; same-month coverage is prohibited.",
            },
            {
                "feature_group": "SNAP",
                "status": "sensitivity only",
                "reason": "Conservative three-month availability lag used, but exact release dates remain unverified.",
            },
            {
                "feature_group": "poverty and MMG",
                "status": "excluded",
                "reason": "No consistent point-in-time history is available for all three outer August folds.",
            },
            {
                "feature_group": "same-month outcomes, coverage, or flags",
                "status": "prohibited",
                "reason": "Unknown at the July 31 cutoff and would leak target-month information.",
            },
        ]
    )
    feature_audit.to_csv(OUTPUT_DIR / "feature_eligibility_audit.csv", index=False)

    manifest = {
        "forecast_cutoff": "2026-07-31",
        "target_month": "2026-08",
        "target_version": TARGET_VERSION,
        "targets": list(METRICS),
        "backtest_years": list(BACKTEST_YEARS),
        "primary_metric": "MAPE (provisional)",
        "secondary_metrics": ["median APE", "MAE", "RMSE", "WAPE"],
        "eligible_counties": len(eligible_fips),
        "selection_rule": "Lower mean MAPE than seasonal naive and lower APE in all three August folds; sensitivity models ineligible.",
        "selected_models": selected,
        "inputs": {
            str(COUNTY_FILE.relative_to(PROJECT_DIR)): sha256(COUNTY_FILE),
            str(STATE_FILE.relative_to(PROJECT_DIR)): sha256(STATE_FILE),
            str(SNAP_FILE.relative_to(PROJECT_DIR)): sha256(SNAP_FILE),
        },
        "versions": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "statsmodels": statsmodels.__version__,
            "lightgbm": lgb.__version__,
        },
        "random_seed": RANDOM_SEED,
    }
    (OUTPUT_DIR / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    write_results_markdown(summary, final, selected)

    print("Selected primary models:", selected)
    print("\nStatewide MAPE by model:")
    print(
        summary.pivot(index="model", columns="metric", values="mape")
        .mul(100)
        .round(2)
        .to_string()
    )
    print("\nSelected August 2026 forecasts:")
    print(
        final.loc[final["selected"], ["metric", "model", "forecast"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
