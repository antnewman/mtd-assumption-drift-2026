"""Deterministic checksumming of drift calculation inputs.

Each drift row stamps an SHA-256 checksum computed over a stable JSON
encoding of its inputs: assumption_id, series_id, baseline_value,
baseline_date, comparison_date, and the list of index values used.
Re-running the calculation with identical inputs produces identical
checksums and identical drift values, so a reader can verify a row was
computed from a specific named set of public inputs.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import Any


def compute_input_checksum(
    *,
    assumption_id: Any,
    series_id: Any | None,
    baseline_value: float,
    baseline_date: date,
    comparison_date: date,
    index_values: list[tuple[date, float]] | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    """Return an SHA-256 hex digest of the drift calculation inputs.

    Parameters
    ----------
    assumption_id, series_id:
        UUID-like identifiers. Converted to strings for JSON encoding.
        ``series_id`` may be None (for example, on a calculation that
        does not reference an external series).
    baseline_value:
        The HMRC assumption value at its baseline date.
    baseline_date, comparison_date:
        Dates used on either side of the reprice or check.
    index_values:
        Optional list of (date, value) tuples for the index
        observations consumed. Included in the digest so that choosing
        a different index month range produces a different checksum.
    extra:
        Optional additional key-value pairs to include in the digest
        (for example, the name of the reprice formula used).

    Returns
    -------
    str
        64-character hex digest.
    """
    payload: dict[str, Any] = {
        "assumption_id": str(assumption_id),
        "series_id": str(series_id) if series_id is not None else None,
        "baseline_value": _round(baseline_value),
        "baseline_date": baseline_date.isoformat(),
        "comparison_date": comparison_date.isoformat(),
    }
    if index_values is not None:
        payload["index_values"] = [
            [d.isoformat(), _round(v)] for d, v in sorted(index_values)
        ]
    if extra:
        for key in sorted(extra):
            payload[key] = extra[key]

    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _round(value: float, places: int = 6) -> float:
    """Round a float to a fixed precision for stable JSON encoding."""
    return round(float(value), places)
