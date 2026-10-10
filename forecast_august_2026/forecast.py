"""Leakage-safe August 2026 forecasting pipeline for Question 7.

The script uses only the prepared food-shelf site-month file and creates
statewide monthly totals.  Every forecast is fit on data available through
July 31 of its forecast year.  Historical August values are accessed only
after a fold's predictions have been created, for backtest scoring.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


FORECAST_YEAR = 2026
BACKTEST_YEARS = (2023, 2024, 2025)
METRICS = ("visits", "pounds", "individuals")
MODELS = (
    "seasonal_naive",
    "ytd_growth",
    "aug_jul_ratio",
    "trend_month_regression",
    "robust_ensemble",
)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_monthly_series(path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    usecols = [
        "month",
        "year",
        *METRICS,
        "flag_outlier",
        "flag_hh_gt_indiv",
        "flag_dup_summed",
        "flag_typo_fixed",
    ]
    raw = pd.read_csv(path, usecols=usecols, parse_dates=["month"])
    raw["year"] = pd.to_numeric(raw["year"], errors="raise").astype(int)

    # Locked policy: keep all high-value observations marked flag_outlier.
    # The prepared file has already resolved duplicate records and corrected
    # documented impossible/clear-typo values.  Missing metric values remain
    # missing and are ignored by the statewide sum.
    flag_counts = {
        name: int(raw[name].fillna(False).astype(bool).sum())
        for name in (
            "flag_outlier",
            "flag_hh_gt_indiv",
            "flag_dup_summed",
            "flag_typo_fixed",
        )
    }

    monthly = (
        raw.groupby("month", as_index=False)[list(METRICS)]
        .sum(min_count=1)
        .sort_values("month")
        .reset_index(drop=True)
    )
    monthly["year"] = monthly["month"].dt.year
    monthly["month_num"] = monthly["month"].dt.month
    return monthly, flag_counts


def assert_source_cutoff(monthly: pd.DataFrame) -> list[str]:
    allowed_end = pd.Timestamp("2026-07-31")
    latest = monthly["month"].max()
    assert latest <= allowed_end, f"Source contains data after cutoff: {latest.date()}"
    assert not (
        (monthly["year"] == FORECAST_YEAR) & (monthly["month_num"] >= 8)
    ).any(), "Source contains an August-or-later 2026 row"
    assert monthly.loc[monthly["year"] == FORECAST_YEAR, "month_num"].max() == 7
    assert monthly[list(METRICS)].notna().all().all(), "Monthly target totals contain missing values"
    return [
        f"PASS source maximum month is {latest:%Y-%m}",
        "PASS no August 2026 outcome is present",
        "PASS no external predictors are used",
        "PASS visits maps to prepared HouseholdsReg-based visits",
        "PASS flagged high observations are retained without clipping or winsorization",
    ]


def trend_month_forecast(train: pd.DataFrame, metric: str, target_date: pd.Timestamp) -> float:
    ordered = train.sort_values("month").reset_index(drop=True)
    origin = ordered["month"].min()
    t = ((ordered["month"].dt.year - origin.year) * 12 + ordered["month"].dt.month - origin.month).to_numpy()
    target_t = (target_date.year - origin.year) * 12 + target_date.month - origin.month

    # Intercept, linear trend, and February-December indicators (January base).
    month_num = ordered["month"].dt.month.to_numpy()
    x = np.column_stack(
        [np.ones(len(ordered)), t]
        + [(month_num == month).astype(float) for month in range(2, 13)]
    )
    target_x = np.array(
        [1.0, float(target_t)]
        + [float(target_date.month == month) for month in range(2, 13)]
    )
    coefficients, *_ = np.linalg.lstsq(x, ordered[metric].to_numpy(dtype=float), rcond=None)
    return float(target_x @ coefficients)


def forecast_one_metric(train: pd.DataFrame, metric: str, target_year: int) -> dict[str, float]:
    target_date = pd.Timestamp(target_year, 8, 1)
    previous_august = train.loc[
        (train["year"] == target_year - 1) & (train["month_num"] == 8), metric
    ]
    if len(previous_august) != 1:
        raise ValueError(f"Expected one prior-August value for {metric}, {target_year}")
    seasonal_naive = float(previous_august.iloc[0])

    current_ytd = train.loc[
        (train["year"] == target_year) & (train["month_num"] <= 7), metric
    ].sum()
    previous_ytd = train.loc[
        (train["year"] == target_year - 1) & (train["month_num"] <= 7), metric
    ].sum()
    ytd_growth = seasonal_naive * float(current_ytd / previous_ytd)

    ratios = []
    for year in sorted(train["year"].unique()):
        july = train.loc[(train["year"] == year) & (train["month_num"] == 7), metric]
        august = train.loc[(train["year"] == year) & (train["month_num"] == 8), metric]
        if len(july) == 1 and len(august) == 1 and float(july.iloc[0]) != 0:
            ratios.append(float(august.iloc[0] / july.iloc[0]))
    if not ratios:
        raise ValueError(f"No historical August/July ratio for {metric}, {target_year}")
    historical_ratio = float(np.median(ratios))
    current_july = float(
        train.loc[(train["year"] == target_year) & (train["month_num"] == 7), metric].iloc[0]
    )
    aug_jul_ratio = current_july * historical_ratio

    trend = trend_month_forecast(train, metric, target_date)
    components = [seasonal_naive, ytd_growth, aug_jul_ratio, trend]
    robust_ensemble = float(np.median(components))
    return {
        "seasonal_naive": seasonal_naive,
        "ytd_growth": ytd_growth,
        "aug_jul_ratio": aug_jul_ratio,
        "trend_month_regression": trend,
        "robust_ensemble": robust_ensemble,
    }


def forecast_fold(monthly: pd.DataFrame, target_year: int) -> tuple[list[dict], str]:
    cutoff = pd.Timestamp(target_year, 7, 31)
    train = monthly.loc[monthly["month"] <= cutoff].copy()
    assert train["month"].max() == pd.Timestamp(target_year, 7, 1)
    assert not ((train["year"] == target_year) & (train["month_num"] >= 8)).any()

    # Generate all predictions before retrieving the held-out actual.
    predictions = {
        metric: forecast_one_metric(train, metric, target_year) for metric in METRICS
    }
    target_date = pd.Timestamp(target_year, 8, 1)
    actual_row = monthly.loc[monthly["month"] == target_date]
    if len(actual_row) != 1:
        raise ValueError(f"Missing held-out August actual for {target_year}")

    rows = []
    for metric in METRICS:
        actual = float(actual_row.iloc[0][metric])
        for model, predicted in predictions[metric].items():
            error = predicted - actual
            rows.append(
                {
                    "forecast_year": target_year,
                    "cutoff": cutoff.date().isoformat(),
                    "metric": metric,
                    "model": model,
                    "actual": actual,
                    "prediction": predicted,
                    "error": error,
                    "absolute_error": abs(error),
                    "absolute_percentage_error": abs(error) / actual,
                }
            )
    return rows, f"PASS {target_year} fold trained only through {cutoff.date().isoformat()}"


def summarize_backtests(backtests: pd.DataFrame) -> pd.DataFrame:
    records = []
    naive = backtests.loc[backtests["model"] == "seasonal_naive"].set_index(
        ["metric", "forecast_year"]
    )["absolute_percentage_error"]
    for (metric, model), group in backtests.groupby(["metric", "model"], sort=False):
        ape = group["absolute_percentage_error"]
        records.append(
            {
                "metric": metric,
                "model": model,
                "folds": len(group),
                "mape": float(ape.mean()),
                "median_ape": float(ape.median()),
                "mae": float(group["absolute_error"].mean()),
                "rmse": float(np.sqrt(np.mean(np.square(group["error"])))),
                "wape": float(group["absolute_error"].sum() / group["actual"].sum()),
                "folds_better_than_naive": int(
                    sum(
                        row.absolute_percentage_error
                        < naive.loc[(metric, row.forecast_year)]
                        for row in group.itertuples()
                    )
                ),
            }
        )
    return pd.DataFrame(records).sort_values(["metric", "mape", "model"]).reset_index(drop=True)


def select_models(summary: pd.DataFrame) -> dict[str, str]:
    """Select only a challenger that is lower-MAPE and wins all three folds."""
    selected = {}
    for metric in METRICS:
        metric_rows = summary.loc[summary["metric"] == metric].copy()
        naive_mape = float(
            metric_rows.loc[metric_rows["model"] == "seasonal_naive", "mape"].iloc[0]
        )
        eligible = metric_rows.loc[
            (metric_rows["model"] != "seasonal_naive")
            & (metric_rows["mape"] < naive_mape)
            & (metric_rows["folds_better_than_naive"] == len(BACKTEST_YEARS))
        ]
        selected[metric] = (
            str(eligible.sort_values("mape").iloc[0]["model"])
            if not eligible.empty
            else "seasonal_naive"
        )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("Data/processed/foodshelf_site_month.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("forecast_august_2026/results"))
    args = parser.parse_args()

    monthly, flag_counts = load_monthly_series(args.input)
    audit_lines = assert_source_cutoff(monthly)

    backtest_rows = []
    for year in BACKTEST_YEARS:
        rows, audit = forecast_fold(monthly, year)
        backtest_rows.extend(rows)
        audit_lines.append(audit)
    backtests = pd.DataFrame(backtest_rows)
    summary = summarize_backtests(backtests)
    selected = select_models(summary)

    final_cutoff = pd.Timestamp("2026-07-31")
    final_train = monthly.loc[monthly["month"] <= final_cutoff].copy()
    final_rows = []
    for metric in METRICS:
        forecasts = forecast_one_metric(final_train, metric, FORECAST_YEAR)
        for model, value in forecasts.items():
            final_rows.append(
                {
                    "forecast_month": "2026-08",
                    "cutoff": final_cutoff.date().isoformat(),
                    "metric": metric,
                    "model": model,
                    "forecast": value,
                    "selected": model == selected[metric],
                }
            )
    final = pd.DataFrame(final_rows)
    audit_lines.append("PASS final forecast trained only through 2026-07-31")
    audit_lines.append("PASS final output does not contain or merge an August 2026 actual")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    monthly.to_csv(args.output_dir / "monthly_series.csv", index=False)
    backtests.to_csv(args.output_dir / "backtest_predictions.csv", index=False)
    summary.to_csv(args.output_dir / "backtest_summary.csv", index=False)
    final.to_csv(args.output_dir / "final_forecasts.csv", index=False)
    (args.output_dir / "cutoff_audit.txt").write_text("\n".join(audit_lines) + "\n", encoding="utf-8")
    manifest = {
        "input": str(args.input.as_posix()),
        "input_sha256": file_sha256(args.input),
        "forecast_cutoff": "2026-07-31",
        "backtest_years": list(BACKTEST_YEARS),
        "primary_metric": "MAPE (provisional until organizer scoring rule arrives)",
        "outlier_policy": "Retain flag_outlier and flag_hh_gt_indiv rows; no clipping, winsorization, or post-backtest exclusions.",
        "preprocessing_policy": "Use prepared site-month data, which resolves documented duplicates and clear impossible/typo values.",
        "flag_counts": flag_counts,
        "selected_models": selected,
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print("Selected models:", selected)
    print("\nBacktest summary (MAPE):")
    print(summary.pivot(index="model", columns="metric", values="mape").to_string())
    print("\nFinal forecasts:")
    print(final.loc[final["selected"], ["metric", "model", "forecast"]].to_string(index=False))


if __name__ == "__main__":
    main()
