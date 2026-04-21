"""Drift calculation runner.

Loads assumptions and external observations from Supabase, runs the
five scoring steps, and writes one ``mtd_2026.drift_calculations`` row
per executed step. Steps whose required data is not yet loaded are
recorded as skipped with a clear reason.

Default comparison date is the first day of the month preceding the
current run date (so that D7F5 publication lag does not cause missing
observations). Override via ``run_drift_calculations(comparison_date=...)``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import UUID

from ..config import Config
from ..supabase_writer import DriftCalculation, SupabaseWriter
from .reprice import (
    RepriceResult,
    reprice_aggregate_cost,
    reprice_transitional_cost,
)

logger = logging.getLogger(__name__)

# Series code used for the services CPI reprice in §6.1 and §6.2.
SERVICES_CPI_INDEX_SERIES_CODE = "ONS-D7F5"

# Assumption keys relevant to each scoring step.
PRIMARY_COST_KEY = "transitional_cost_50k_cohort"
AGGREGATE_COST_KEY = "transitional_cost_total_30k_plus"
POPULATION_KEY = "population_50k_cohort"
TAX_GAP_KEY = "self_assessment_tax_gap"
ROI_KEY = "programme_roi"


@dataclass(frozen=True)
class DriftRunResult:
    """Per-scoring-step outcome for a drift run."""

    step: str
    status: str  # "executed" or "skipped"
    assumption_key: str | None = None
    drift_absolute: float | None = None
    drift_percent: float | None = None
    row_id: str | None = None
    skip_reason: str | None = None


@dataclass
class _AssumptionRow:
    id: UUID
    assumption_key: str
    value: float
    baseline_date: date


def run_drift_calculations(
    *,
    writer: SupabaseWriter | None = None,
    config: Config | None = None,
    comparison_date: date | None = None,
) -> list[DriftRunResult]:
    """Run the five scoring steps, persist results, and return a summary.

    Steps whose required data is not yet loaded are recorded as
    skipped rather than raising. This lets the runner complete §6.1
    and §6.2 even before the non-ONS observations ingest lands.
    """
    if writer is None:
        writer = SupabaseWriter(config=config)
    if comparison_date is None:
        comparison_date = _default_comparison_date()

    assumptions = _load_active_assumptions(writer)
    d7f5_id, d7f5_obs = _load_d7f5(writer)

    results: list[DriftRunResult] = []

    results.append(
        _run_primary_reprice(
            writer=writer,
            assumptions=assumptions,
            d7f5_id=d7f5_id,
            d7f5_observations=d7f5_obs,
            comparison_date=comparison_date,
        )
    )

    results.append(
        _run_aggregate_reprice(
            writer=writer,
            assumptions=assumptions,
            d7f5_id=d7f5_id,
            d7f5_observations=d7f5_obs,
            comparison_date=comparison_date,
        )
    )

    # §6.3 population cross-check: needs BPE observations.
    results.append(
        _skip_step(
            step="§6.3",
            assumption_key=POPULATION_KEY,
            reason=(
                "Requires DBT Business Population Estimates 2025 to be "
                "loaded into pda_shared.external_observations. Pending "
                "non-ONS observations ingest."
            ),
        )
    )

    # §6.4 tax gap consistency check: needs HMRC MTG 2025 observation.
    results.append(
        _skip_step(
            step="§6.4",
            assumption_key=TAX_GAP_KEY,
            reason=(
                "Requires HMRC Measuring Tax Gaps 2025 Self Assessment "
                "tax gap value to be loaded. Pending non-ONS ingest."
            ),
        )
    )

    # §6.5 ROI sensitivity: needs OBR EFO ATR observation and the
    # §6.1 reprice output.
    results.append(
        _skip_step(
            step="§6.5",
            assumption_key=ROI_KEY,
            reason=(
                "Requires OBR EFO March 2026 ATR scorecard value to be "
                "loaded. Pending non-ONS ingest."
            ),
        )
    )

    return results


def _run_primary_reprice(
    *,
    writer: SupabaseWriter,
    assumptions: dict[str, _AssumptionRow],
    d7f5_id: UUID,
    d7f5_observations: list[tuple[date, float]],
    comparison_date: date,
) -> DriftRunResult:
    assumption = assumptions.get(PRIMARY_COST_KEY)
    if assumption is None:
        return _skip_step(
            step="§6.1",
            assumption_key=PRIMARY_COST_KEY,
            reason="Assumption row missing from mtd_2026.assumptions.",
        )

    try:
        result = reprice_transitional_cost(
            assumption_id=assumption.id,
            series_id=d7f5_id,
            baseline_value=assumption.value,
            baseline_date=assumption.baseline_date,
            comparison_date=comparison_date,
            index_observations=d7f5_observations,
        )
    except ValueError as exc:
        return _skip_step(
            step="§6.1",
            assumption_key=PRIMARY_COST_KEY,
            reason=str(exc),
        )

    row = _write_drift_row(
        writer=writer,
        assumption_id=assumption.id,
        series_id=d7f5_id,
        result=result,
    )
    return DriftRunResult(
        step="§6.1",
        status="executed",
        assumption_key=PRIMARY_COST_KEY,
        drift_absolute=result.drift_absolute,
        drift_percent=result.drift_percent,
        row_id=row.get("id"),
    )


def _run_aggregate_reprice(
    *,
    writer: SupabaseWriter,
    assumptions: dict[str, _AssumptionRow],
    d7f5_id: UUID,
    d7f5_observations: list[tuple[date, float]],
    comparison_date: date,
) -> DriftRunResult:
    assumption = assumptions.get(AGGREGATE_COST_KEY)
    if assumption is None:
        return _skip_step(
            step="§6.2",
            assumption_key=AGGREGATE_COST_KEY,
            reason="Assumption row missing from mtd_2026.assumptions.",
        )

    try:
        result = reprice_aggregate_cost(
            assumption_id=assumption.id,
            series_id=d7f5_id,
            baseline_value=assumption.value,
            baseline_date=assumption.baseline_date,
            comparison_date=comparison_date,
            index_observations=d7f5_observations,
        )
    except ValueError as exc:
        return _skip_step(
            step="§6.2",
            assumption_key=AGGREGATE_COST_KEY,
            reason=str(exc),
        )

    row = _write_drift_row(
        writer=writer,
        assumption_id=assumption.id,
        series_id=d7f5_id,
        result=result,
    )
    return DriftRunResult(
        step="§6.2",
        status="executed",
        assumption_key=AGGREGATE_COST_KEY,
        drift_absolute=result.drift_absolute,
        drift_percent=result.drift_percent,
        row_id=row.get("id"),
    )


def _skip_step(*, step: str, assumption_key: str, reason: str) -> DriftRunResult:
    logger.info("Skipping %s (%s): %s", step, assumption_key, reason)
    return DriftRunResult(
        step=step,
        status="skipped",
        assumption_key=assumption_key,
        skip_reason=reason,
    )


def _write_drift_row(
    *,
    writer: SupabaseWriter,
    assumption_id: UUID,
    series_id: UUID,
    result: RepriceResult,
) -> dict[str, Any]:
    calc = DriftCalculation(
        assumption_id=assumption_id,
        series_id=series_id,
        baseline_value=result.baseline_value,
        baseline_date=result.baseline_date,
        comparison_value=result.comparison_value,
        comparison_date=result.comparison_date,
        drift_absolute=result.drift_absolute,
        drift_percent=result.drift_percent,
        methodology_notes=result.methodology_notes,
        confidence="medium",
    )
    return writer.insert_drift_calculation(calc)


def _load_active_assumptions(writer: SupabaseWriter) -> dict[str, _AssumptionRow]:
    resp = (
        writer._client.schema("mtd_2026")
        .table("assumptions")
        .select("id,assumption_key,value,baseline_date,is_superseded")
        .eq("is_superseded", False)
        .execute()
    )
    data = getattr(resp, "data", None) or []
    out: dict[str, _AssumptionRow] = {}
    for row in data:
        out[row["assumption_key"]] = _AssumptionRow(
            id=UUID(row["id"]),
            assumption_key=row["assumption_key"],
            value=float(row["value"]),
            baseline_date=date.fromisoformat(row["baseline_date"]),
        )
    return out


def _load_d7f5(writer: SupabaseWriter) -> tuple[UUID, list[tuple[date, float]]]:
    series_resp = (
        writer._client.schema("pda_shared")
        .table("external_series")
        .select("id,series_code")
        .eq("series_code", SERVICES_CPI_INDEX_SERIES_CODE)
        .limit(1)
        .execute()
    )
    series_data = getattr(series_resp, "data", None) or []
    if not series_data:
        raise RuntimeError(
            f"series_code {SERVICES_CPI_INDEX_SERIES_CODE!r} not found in "
            f"pda_shared.external_series. Run migration 0001 first."
        )
    series_id = UUID(series_data[0]["id"])

    obs_resp = (
        writer._client.schema("pda_shared")
        .table("external_observations")
        .select("observation_date,value")
        .eq("series_id", str(series_id))
        .execute()
    )
    obs_data = getattr(obs_resp, "data", None) or []
    observations = [
        (date.fromisoformat(row["observation_date"]), float(row["value"]))
        for row in obs_data
        if row.get("observation_date") and row.get("value") is not None
    ]
    return series_id, observations


def _default_comparison_date() -> date:
    """Return a comparison date that is safely covered by published ONS data.

    ONS CPI publishes monthly values for month M in the middle of month
    M+1. To be safe, default to the first day of the month TWO months
    before today (that month is certainly published).
    """
    today = date.today()
    year = today.year
    month = today.month - 2
    if month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)
