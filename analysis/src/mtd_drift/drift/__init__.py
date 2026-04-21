"""Drift calculation engine for the MTD investigation.

Implements the five scoring steps defined in methodology §6:

  §6.1  Transitional cost reprice (primary)   -> reprice.py
  §6.2  Total transitional cost reprice       -> reprice.py
  §6.3  Population cross-check                -> cross_check.py
  §6.4  Tax gap consistency check             -> consistency.py
  §6.5  ROI sensitivity                       -> sensitivity.py

§6.3, §6.4, and §6.5 require non-ONS observations (DBT BPE, HMRC MTG,
OBR EFO, BoE Bank Rate) to be present in ``pda_shared.external_observations``.
Until those are loaded by the non-ONS ingest follow-up, the runner
records those scoring steps as skipped with a clear reason.

Each executed scoring step writes one row to
``mtd_2026.drift_calculations`` via the Supabase writer. The row stamps
the inputs it used, the formula applied, the resulting absolute and
percent drift, and a methodology_notes field that identifies the
methodology section and the caveat flags applied.

Determinism: every row carries an SHA-256 checksum computed over the
sorted JSON of its inputs. Re-running the drift calculation with the
same inputs produces identical drift values and identical checksums.
"""

from __future__ import annotations

from .caveats import CaveatFlag
from .checksum import compute_input_checksum
from .reprice import reprice_transitional_cost, reprice_aggregate_cost
from .runner import DriftRunResult, run_drift_calculations

__all__ = [
    "CaveatFlag",
    "DriftRunResult",
    "compute_input_checksum",
    "reprice_transitional_cost",
    "reprice_aggregate_cost",
    "run_drift_calculations",
]
