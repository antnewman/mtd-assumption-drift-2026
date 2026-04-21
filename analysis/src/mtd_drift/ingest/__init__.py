"""External observations ingest for the MTD investigation.

Fetches monthly ONS time series and writes rows to
``pda_shared.external_observations``. Non-ONS manual snapshots
(DBT BPE, HMRC MTG, OBR EFO, BoE Bank Rate) are ingested via
supabase/migrations with user-verified values; they are not handled by
this module.

Entry points:

  - :func:`mtd_drift.ingest.ons_history.fetch_ons_history` fetches the
    full monthly history for an ONS indicator via the public ONS API.
  - :func:`mtd_drift.ingest.runner.run_ons_ingest` orchestrates the
    end-to-end ingest for all four ONS series used in the methodology
    (D7NN, D7F5, D7BT, D7G7), deduplicating against existing rows.

See ``__main__.py`` for the CLI entry point.
"""

from __future__ import annotations

from .ons_history import (
    INDICATOR_MAP,
    ONSObservation,
    SERIES_CODE_BY_INDICATOR,
    fetch_ons_history,
)
from .runner import IngestResult, run_ons_ingest

__all__ = [
    "INDICATOR_MAP",
    "IngestResult",
    "ONSObservation",
    "SERIES_CODE_BY_INDICATOR",
    "fetch_ons_history",
    "run_ons_ingest",
]
