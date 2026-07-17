"""Shared normalization rules for data-info summary metrics."""

from __future__ import annotations

from typing import Any

DEFAULT_DATA_INFO_METRICS = ("obs", "mean", "stderr", "min", "max")
OPTIONAL_DATA_INFO_METRICS = ("med", "q1", "q3", "skewness", "kurtosis")
DATA_INFO_METRICS = DEFAULT_DATA_INFO_METRICS + OPTIONAL_DATA_INFO_METRICS


def normalize_data_info_metrics(value: Any) -> tuple[str, ...]:
    """Keep mandatory metrics and append supported extras in caller order."""
    if value is None:
        return DEFAULT_DATA_INFO_METRICS
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, (list, tuple, set)):
        values = value
    else:
        raise TypeError("Expected a comma-separated string or string collection.")

    additional_metrics: list[str] = []
    for item in values:
        metric = str(item).strip().lower()
        if (
            metric in OPTIONAL_DATA_INFO_METRICS
            and metric not in additional_metrics
        ):
            additional_metrics.append(metric)

    return DEFAULT_DATA_INFO_METRICS + tuple(additional_metrics)
