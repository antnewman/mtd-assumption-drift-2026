"""Methodology caveat flags.

Three mandatory caveats are defined in methodology §7 and must be
disclosed alongside every affected drift row and finding. This module
encodes them as an enum so scoring functions can stamp the applicable
flags into the ``methodology_notes`` field and downstream consumers
can check for them structurally.
"""

from __future__ import annotations

from enum import Enum


class CaveatFlag(str, Enum):
    """Mandatory caveat flags per methodology §7."""

    # §7.1: services CPI vs all-items CPI.
    # Set on any reprice that uses services CPI.
    SERVICES_CPI_CHOSEN = "7.1:services_cpi_chosen"

    # §7.2: Business Population Estimates is classified "official
    # statistics in development", not accredited.
    BPE_IN_DEVELOPMENT = "7.2:bpe_in_development"

    # §7.3: HMRC Measuring Tax Gaps runs approximately two years in
    # arrears; the tax gap check is of consistency, not of drift.
    TAX_GAP_LAG = "7.3:tax_gap_lag"


def format_caveats(flags: list[CaveatFlag]) -> str:
    """Render a sorted, comma-separated list of caveat flag tokens."""
    return ", ".join(sorted(f.value for f in flags))
