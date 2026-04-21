"""Orchestrator for the ONS observations ingest.

Ties :mod:`mtd_drift.ingest.ons_history` (fetcher) to
:mod:`mtd_drift.supabase_writer` (writer) with a dedup step so
re-running the ingest does not create duplicate rows.

Dedup strategy: query the set of
``(series_id, observation_date)`` pairs already present in
``pda_shared.external_observations`` for the target series, then
insert only the observations that do not yet exist. This keeps the
ingest idempotent even though the table has no unique constraint on
the pair (the table is append-only by design, so a unique constraint
would block revisions captured later via ``captured_at``).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date
from uuid import UUID

from ..config import Config
from ..supabase_writer import ExternalObservation, SupabaseWriter
from .ons_history import (
    INDICATOR_MAP,
    SERIES_CODE_BY_INDICATOR,
    ONSObservation,
    fetch_ons_history,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestResult:
    """Summary of one indicator's ingest run."""

    indicator: str
    series_code: str
    fetched: int
    already_present: int
    inserted: int


@dataclass(frozen=True)
class SeriesRow:
    """Subset of ``pda_shared.external_series`` fields we need."""

    id: UUID
    series_code: str


def run_ons_ingest(
    *,
    writer: SupabaseWriter | None = None,
    config: Config | None = None,
    since: date = date(2021, 1, 1),
    indicators: list[str] | None = None,
) -> list[IngestResult]:
    """Run the ingest end-to-end for the four ONS indicators.

    Parameters
    ----------
    writer:
        A :class:`SupabaseWriter`. If omitted, one is constructed from
        the default configuration.
    config:
        A :class:`Config`. Only used when ``writer`` is omitted.
    since:
        Lower bound on observation dates. Default is 2021-01-01, which
        aligns with the pricing base year of the transitional cost
        assumption under investigation.
    indicators:
        Override the list of indicators to ingest. Default is all four
        ONS series registered in :data:`SERIES_CODE_BY_INDICATOR`.

    Returns
    -------
    list[IngestResult]
        One result per indicator.
    """
    if writer is None:
        writer = SupabaseWriter(config=config)
    if indicators is None:
        indicators = list(SERIES_CODE_BY_INDICATOR)

    results: list[IngestResult] = []
    for indicator in indicators:
        if indicator not in SERIES_CODE_BY_INDICATOR:
            raise ValueError(
                f"Indicator {indicator!r} is not configured for this ingest. "
                f"Expected one of {sorted(SERIES_CODE_BY_INDICATOR)}."
            )

        series_code = SERIES_CODE_BY_INDICATOR[indicator]
        logger.info("Ingesting %s (series_code=%s)", indicator, series_code)

        series_row = _lookup_series(writer, series_code)
        observations = fetch_ons_history(indicator, since=since)
        already = _existing_dates(writer, series_row.id)
        new_obs = [o for o in observations if o.observation_date not in already]

        if new_obs:
            rows = [
                ExternalObservation(
                    series_id=series_row.id,
                    observation_date=o.observation_date,
                    value=o.value,
                    notes=_note_for(indicator),
                )
                for o in new_obs
            ]
            _batch_insert(writer, rows)

        results.append(
            IngestResult(
                indicator=indicator,
                series_code=series_code,
                fetched=len(observations),
                already_present=len(observations) - len(new_obs),
                inserted=len(new_obs),
            )
        )

        logger.info(
            "%s: fetched=%d already_present=%d inserted=%d",
            indicator,
            len(observations),
            len(observations) - len(new_obs),
            len(new_obs),
        )

    return results


def _lookup_series(writer: SupabaseWriter, series_code: str) -> SeriesRow:
    resp = (
        writer._client.schema("pda_shared")
        .table("external_series")
        .select("id,series_code")
        .eq("series_code", series_code)
        .limit(1)
        .execute()
    )
    data = getattr(resp, "data", None) or []
    if not data:
        raise RuntimeError(
            f"series_code {series_code!r} not found in pda_shared.external_series. "
            f"Run migration 0001_mtd_2026_seed_initial_data first."
        )
    row = data[0]
    return SeriesRow(id=UUID(row["id"]), series_code=row["series_code"])


def _existing_dates(writer: SupabaseWriter, series_id: UUID) -> set[date]:
    resp = (
        writer._client.schema("pda_shared")
        .table("external_observations")
        .select("observation_date")
        .eq("series_id", str(series_id))
        .execute()
    )
    data = getattr(resp, "data", None) or []
    dates: set[date] = set()
    for row in data:
        value = row.get("observation_date")
        if not value:
            continue
        dates.add(date.fromisoformat(value))
    return dates


def _batch_insert(
    writer: SupabaseWriter,
    observations: list[ExternalObservation],
) -> None:
    """Insert observations in a single batch call.

    Using supabase-py's batch insert avoids one round trip per row.
    Failures bubble up as RuntimeError via the underlying client.
    """
    payload = [
        {
            "series_id": str(o.series_id),
            "observation_date": o.observation_date.isoformat(),
            "value": o.value,
            "notes": o.notes,
        }
        for o in observations
    ]
    resp = (
        writer._client.schema("pda_shared")
        .table("external_observations")
        .insert(payload)
        .execute()
    )
    data = getattr(resp, "data", None)
    if not data or len(data) != len(observations):
        raise RuntimeError(
            f"Batch insert returned {len(data) if data else 0} rows; "
            f"expected {len(observations)}."
        )


def _note_for(indicator: str) -> str:
    _dataset, ts, unit, desc = INDICATOR_MAP[indicator]
    return (
        f"ONS {ts} via ONS timeseries API (dataset MM23). "
        f"{desc}. Unit: {unit}. "
        f"Fetched by mtd-drift-analysis/ingest."
    )
