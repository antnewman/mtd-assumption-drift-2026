"""Findings populator for the MTD investigation.

Reads the markdown templates in ``findings/`` and inserts rows into
``mtd_2026.findings`` with ``published = false`` and
``supporting_drift_ids`` populated from the most recent matching row
in ``mtd_2026.drift_calculations``.

A finding whose matching drift row does not exist (typically because
the non-ONS observations have not been ingested yet) is skipped with
a clear reason.
"""

from __future__ import annotations

from .populate import (
    FindingTemplate,
    PopulateResult,
    parse_finding_file,
    populate_findings,
)

__all__ = [
    "FindingTemplate",
    "PopulateResult",
    "parse_finding_file",
    "populate_findings",
]
