"""Typed insert helpers for the MTD investigation's Supabase schema.

Writes rows to three append-only tables:

  - ``pda_shared.external_observations``
  - ``mtd_2026.drift_calculations``
  - ``mtd_2026.findings``

Schema changes are not performed here; they belong in
``supabase/migrations/`` and are applied via the Supabase MCP
``apply_migration`` tool. This module is data-layer only.

The service role key is never logged by this module. ``SupabaseWriter``
deliberately does not expose the key in ``repr``, and the underlying
``supabase-py`` client does not log credentials either.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from supabase import Client, create_client

from .config import Config


@dataclass(frozen=True)
class ExternalObservation:
    """One row to insert into ``pda_shared.external_observations``."""

    series_id: UUID
    observation_date: date
    value: float
    notes: str | None = None


@dataclass(frozen=True)
class DriftCalculation:
    """One row to insert into ``mtd_2026.drift_calculations``.

    Every drift row stamps the inputs it used, the formula applied, and
    the resulting absolute and percent drift. ``methodology_notes``
    identifies the methodology section (for example "§6.1 services CPI
    reprice") and lists any mandatory caveat flags that apply (§7.1,
    §7.2, §7.3).
    """

    assumption_id: UUID
    series_id: UUID | None
    baseline_value: float
    baseline_date: date
    comparison_value: float
    comparison_date: date
    drift_absolute: float
    drift_percent: float
    methodology_notes: str
    confidence: str
    notes: str | None = None


@dataclass(frozen=True)
class Finding:
    """One row to insert into ``mtd_2026.findings``.

    ``published`` defaults to False. A finding does not become public
    until an approved review row exists in ``pda_shared.reviews`` and
    the ``published`` flag is flipped in a separate, explicit step.
    """

    finding_key: str
    headline: str
    narrative: str
    magnitude: str
    direction: str
    confidence: str
    caveats: str
    supporting_drift_ids: list[UUID] | None = None
    published: bool = False


class SupabaseWriter:
    """Writes rows to the pda-investigations Supabase project.

    Takes a ``Config`` (or loads one from the environment) and creates
    a supabase-py client under the hood. One instance may be reused
    across many inserts within a run.
    """

    def __init__(self, config: Config | None = None) -> None:
        self._config = config or Config.from_env()
        self._client: Client = create_client(
            self._config.supabase_url,
            self._config.supabase_service_role_key,
        )

    def __repr__(self) -> str:
        return (
            f"SupabaseWriter(supabase_url={self._config.supabase_url!r}, "
            f"supabase_service_role_key=<redacted>)"
        )

    def insert_external_observation(self, obs: ExternalObservation) -> dict[str, Any]:
        """Insert into ``pda_shared.external_observations`` and return the row."""
        payload = {
            "series_id": str(obs.series_id),
            "observation_date": obs.observation_date.isoformat(),
            "value": obs.value,
            "notes": obs.notes,
        }
        resp = (
            self._client.schema("pda_shared")
            .table("external_observations")
            .insert(payload)
            .execute()
        )
        return _first_row(resp)

    def insert_drift_calculation(self, calc: DriftCalculation) -> dict[str, Any]:
        """Insert into ``mtd_2026.drift_calculations`` and return the row."""
        payload = {
            "assumption_id": str(calc.assumption_id),
            "series_id": str(calc.series_id) if calc.series_id else None,
            "baseline_value": calc.baseline_value,
            "baseline_date": calc.baseline_date.isoformat(),
            "comparison_value": calc.comparison_value,
            "comparison_date": calc.comparison_date.isoformat(),
            "drift_absolute": calc.drift_absolute,
            "drift_percent": calc.drift_percent,
            "methodology_notes": calc.methodology_notes,
            "confidence": calc.confidence,
            "notes": calc.notes,
        }
        resp = (
            self._client.schema("mtd_2026")
            .table("drift_calculations")
            .insert(payload)
            .execute()
        )
        return _first_row(resp)

    def insert_finding(self, finding: Finding) -> dict[str, Any]:
        """Insert into ``mtd_2026.findings`` and return the row.

        ``published`` is whatever the caller passed (default False).
        The writer does not enforce the reviewer gate itself; that is
        enforced at the orchestration layer (the publish step in PR 5
        and beyond).
        """
        payload = {
            "finding_key": finding.finding_key,
            "headline": finding.headline,
            "narrative": finding.narrative,
            "magnitude": finding.magnitude,
            "direction": finding.direction,
            "confidence": finding.confidence,
            "caveats": finding.caveats,
            "supporting_drift_ids": (
                [str(x) for x in finding.supporting_drift_ids]
                if finding.supporting_drift_ids
                else None
            ),
            "published": finding.published,
        }
        resp = (
            self._client.schema("mtd_2026")
            .table("findings")
            .insert(payload)
            .execute()
        )
        return _first_row(resp)


def _first_row(resp: Any) -> dict[str, Any]:
    """Return the first inserted row from a supabase-py response.

    Supabase returns a list of inserted rows on success. We only ever
    insert a single row per call, so pull the first element. If the
    response is empty, raise a clear error rather than returning None.
    """
    data = getattr(resp, "data", None)
    if not data:
        raise RuntimeError(
            f"Supabase insert returned no rows. Response: {resp!r}"
        )
    return data[0]
