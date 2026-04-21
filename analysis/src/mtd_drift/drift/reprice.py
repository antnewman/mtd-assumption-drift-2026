"""Transitional cost reprice for methodology §6.1 and §6.2.

The HMRC assumption ``transitional_cost_50k_cohort`` (£285 per
above-£50k-cohort business) and ``transitional_cost_total_30k_plus``
(£561m total for the above-£30k population) are stated in 2021 prices
on the February 2024 TIIN baseline date. Repricing uses the ONS
services CPI index (D7F5), aligned with methodology §7.1.

The "2021 prices" convention is implemented here as the arithmetic
mean of the monthly D7F5 index values across calendar year 2021. This
is the most defensible reading of "2021 prices" when the TIIN does not
specify a particular month.

The reprice itself is a simple index ratio:

    current_price_equivalent = baseline_value * (index_cmp / index_base)

where ``index_base`` is the 2021 annual mean and ``index_cmp`` is the
D7F5 value for the comparison month (default: March 2026 for a
pre-mandation indicative figure; April 2026 when that value publishes).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import mean

from .caveats import CaveatFlag, format_caveats
from .checksum import compute_input_checksum


@dataclass(frozen=True)
class RepriceResult:
    """Output of a single reprice calculation."""

    baseline_value: float
    baseline_date: date
    comparison_value: float
    comparison_date: date
    drift_absolute: float
    drift_percent: float
    index_base: float
    index_comparison: float
    index_values_used: list[tuple[date, float]]
    caveats: list[CaveatFlag]
    methodology_notes: str
    input_checksum: str


def reprice_transitional_cost(
    *,
    assumption_id,
    series_id,
    baseline_value: float,
    baseline_date: date,
    comparison_date: date,
    index_observations: list[tuple[date, float]],
    base_year: int = 2021,
) -> RepriceResult:
    """Reprice the £285 transitional cost to a current-price equivalent.

    Applies methodology §6.1. Caveat §7.1 is stamped because services
    CPI is the chosen index.

    Parameters
    ----------
    assumption_id, series_id:
        Identifiers used to stamp the drift row; not used in the
        arithmetic itself.
    baseline_value:
        The HMRC assumption (£285).
    baseline_date:
        The TIIN publication or republication date.
    comparison_date:
        The month to reprice to (typically March or April 2026).
    index_observations:
        Monthly D7F5 values, each as ``(first-of-month, index)``. Must
        cover both the base year and the comparison month.
    base_year:
        Year to average for the base index. Default 2021 (the TIIN's
        pricing base year for the compliance cost).

    Returns
    -------
    RepriceResult
    """
    index_base, base_months = _annual_mean(index_observations, base_year)
    index_cmp = _value_at(index_observations, comparison_date)

    current = baseline_value * (index_cmp / index_base)
    drift_absolute = current - baseline_value
    drift_percent = drift_absolute / baseline_value * 100.0

    caveats = [CaveatFlag.SERVICES_CPI_CHOSEN]
    used = sorted(base_months + [(comparison_date, index_cmp)])

    notes = (
        f"§6.1 services CPI reprice using ONS D7F5 "
        f"(base: mean of {base_year} monthly indices = {index_base:.2f}; "
        f"comparison {comparison_date.isoformat()}: {index_cmp:.2f}). "
        f"Caveat flags: {format_caveats(caveats)}."
    )

    checksum = compute_input_checksum(
        assumption_id=assumption_id,
        series_id=series_id,
        baseline_value=baseline_value,
        baseline_date=baseline_date,
        comparison_date=comparison_date,
        index_values=used,
        extra={"formula": "§6.1", "base_year": base_year},
    )

    return RepriceResult(
        baseline_value=baseline_value,
        baseline_date=baseline_date,
        comparison_value=current,
        comparison_date=comparison_date,
        drift_absolute=drift_absolute,
        drift_percent=drift_percent,
        index_base=index_base,
        index_comparison=index_cmp,
        index_values_used=used,
        caveats=caveats,
        methodology_notes=notes + f" Input checksum: {checksum}.",
        input_checksum=checksum,
    )


def reprice_aggregate_cost(
    *,
    assumption_id,
    series_id,
    baseline_value: float,
    baseline_date: date,
    comparison_date: date,
    index_observations: list[tuple[date, float]],
    base_year: int = 2021,
) -> RepriceResult:
    """Reprice the £561m aggregate transitional cost.

    Applies methodology §6.2. The formula is identical to §6.1; only
    the notes differ to reflect that this is the aggregate check
    rather than the primary per-business reprice.
    """
    index_base, base_months = _annual_mean(index_observations, base_year)
    index_cmp = _value_at(index_observations, comparison_date)

    current = baseline_value * (index_cmp / index_base)
    drift_absolute = current - baseline_value
    drift_percent = drift_absolute / baseline_value * 100.0

    caveats = [CaveatFlag.SERVICES_CPI_CHOSEN]
    used = sorted(base_months + [(comparison_date, index_cmp)])

    notes = (
        f"§6.2 aggregate transitional cost reprice using ONS D7F5 "
        f"(base: mean of {base_year} monthly indices = {index_base:.2f}; "
        f"comparison {comparison_date.isoformat()}: {index_cmp:.2f}). "
        f"Caveat flags: {format_caveats(caveats)}."
    )

    checksum = compute_input_checksum(
        assumption_id=assumption_id,
        series_id=series_id,
        baseline_value=baseline_value,
        baseline_date=baseline_date,
        comparison_date=comparison_date,
        index_values=used,
        extra={"formula": "§6.2", "base_year": base_year},
    )

    return RepriceResult(
        baseline_value=baseline_value,
        baseline_date=baseline_date,
        comparison_value=current,
        comparison_date=comparison_date,
        drift_absolute=drift_absolute,
        drift_percent=drift_percent,
        index_base=index_base,
        index_comparison=index_cmp,
        index_values_used=used,
        caveats=caveats,
        methodology_notes=notes + f" Input checksum: {checksum}.",
        input_checksum=checksum,
    )


def _annual_mean(
    observations: list[tuple[date, float]],
    year: int,
) -> tuple[float, list[tuple[date, float]]]:
    """Return the arithmetic mean of monthly values in ``year``.

    Also returns the list of ``(date, value)`` tuples used, for the
    checksum and the audit trail.

    Raises
    ------
    ValueError
        If fewer than 12 monthly values are available for ``year``.
    """
    months = sorted(
        (d, v) for d, v in observations if d.year == year
    )
    if len(months) < 12:
        raise ValueError(
            f"Need 12 monthly observations for {year}; got {len(months)}. "
            f"Run the ONS ingest (python -m mtd_drift.ingest) to populate "
            f"pda_shared.external_observations."
        )
    return mean(v for _d, v in months), months


def _value_at(
    observations: list[tuple[date, float]],
    target: date,
) -> float:
    """Return the observation value at exactly ``target``.

    Raises
    ------
    ValueError
        If the target date is not present in the observations.
    """
    for d, v in observations:
        if d == target:
            return v
    raise ValueError(
        f"No observation for {target.isoformat()} in the provided series. "
        f"Check that the ingest has populated this month."
    )
