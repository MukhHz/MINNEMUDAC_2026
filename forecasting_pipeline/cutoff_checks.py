"""Reusable point-in-time checks for the August forecasting pipeline."""

from __future__ import annotations

import pandas as pd


def assert_information_cutoff(
    frame: pd.DataFrame,
    cutoff: str | pd.Timestamp,
    *,
    observation_date_col: str,
    availability_date_col: str | None = None,
    frame_name: str = "features",
) -> None:
    """Raise ValueError when a row was observed or available after cutoff."""
    cutoff_ts = pd.Timestamp(cutoff)
    observation_dates = pd.to_datetime(frame[observation_date_col], errors="coerce")

    if observation_dates.isna().any():
        raise ValueError(f"{frame_name}: invalid observation dates found.")

    late_observations = observation_dates.gt(cutoff_ts)
    if late_observations.any():
        latest = observation_dates.loc[late_observations].max()
        raise ValueError(
            f"{frame_name}: observation date {latest.date()} exceeds "
            f"cutoff {cutoff_ts.date()}."
        )

    if availability_date_col is not None:
        availability_dates = pd.to_datetime(
            frame[availability_date_col], errors="coerce"
        )
        if availability_dates.isna().any():
            raise ValueError(f"{frame_name}: invalid availability dates found.")
        late_availability = availability_dates.gt(cutoff_ts)
        if late_availability.any():
            latest = availability_dates.loc[late_availability].max()
            raise ValueError(
                f"{frame_name}: information available on {latest.date()} "
                f"exceeds cutoff {cutoff_ts.date()}."
            )


def assert_no_target_month(
    frame: pd.DataFrame,
    target_month: str | pd.Timestamp,
    *,
    date_col: str,
    frame_name: str = "training data",
) -> None:
    """Ensure the held-out target month is absent from a training frame."""
    target_period = pd.Timestamp(target_month).to_period("M")
    periods = pd.to_datetime(frame[date_col], errors="coerce").dt.to_period("M")
    if periods.eq(target_period).any():
        raise ValueError(
            f"{frame_name}: held-out month {target_period} is present."
        )

