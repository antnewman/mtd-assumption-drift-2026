"""MTD assumption drift: analysis package.

Orchestrates the analytical phases of the investigation:

  1. External observations ingest     (mtd_drift.ingest, PR 3)
  2. Drift calculations               (mtd_drift.drift, PR 4)
  3. Findings draft                   (mtd_drift.findings, PR 5)

The data store is Supabase project ``bulheatuxvktopxrwbvs``
(``pda-investigations``, eu-west-2 London region). External time series
are fetched via the PDA Platform
(https://github.com/antnewman/pda-platform). See the repository README
and ``methodology.md`` in the parent repo for the full context.
"""

from __future__ import annotations

from .config import Config
from .supabase_writer import (
    DriftCalculation,
    ExternalObservation,
    Finding,
    SupabaseWriter,
)

__all__ = [
    "Config",
    "DriftCalculation",
    "ExternalObservation",
    "Finding",
    "SupabaseWriter",
]

__version__ = "0.1.0"
