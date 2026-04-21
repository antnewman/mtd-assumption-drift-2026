"""ONS time-series history fetcher.

Provides the full monthly history for an ONS series from the public
ONS timeseries API. The investigation needs a price-level history, not
just the latest value, so this module calls the ONS endpoint directly.
The URL pattern mirrors pda-platform's ``pm_assumptions._fetch_ons``
so the provenance chain is the same.

The four indicator keys supported here align with pda-platform v1.2.1
and onwards, where the services CPI series (D7NN, D7F5) and the
all-items index (D7BT) were added.

A pda-platform enhancement that exposes history as a first-class MCP
tool is a natural follow-up; this module would then become a thin
wrapper over that tool.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime


# Indicator key -> (dataset, timeseries, unit, description).
# Aligned with pda-platform's ``pm_assumptions._fetch_ons`` ONS_DATASETS
# map. When pda-platform extends its indicators, keep this mapping in
# sync.
INDICATOR_MAP: dict[str, tuple[str, str, str, str]] = {
    "services_cpi_rate": (
        "MM23",
        "D7NN",
        "% annual",
        "UK CPI services annual inflation rate",
    ),
    "services_cpi_index": (
        "MM23",
        "D7F5",
        "index (2015=100)",
        "UK CPI services index, 2015=100",
    ),
    "all_items_cpi_rate": (
        "MM23",
        "D7G7",
        "% annual",
        "UK CPI all-items annual inflation rate",
    ),
    "all_items_cpi_index": (
        "MM23",
        "D7BT",
        "index (2015=100)",
        "UK CPI all-items index, 2015=100",
    ),
}


# Maps ingest indicator keys to the Supabase ``series_code`` values
# that were seeded into ``pda_shared.external_series`` in migration
# 0001. The series_code is what Supabase rows reference; the indicator
# key is what this module uses internally for readability.
SERIES_CODE_BY_INDICATOR: dict[str, str] = {
    "services_cpi_rate": "ONS-D7NN",
    "services_cpi_index": "ONS-D7F5",
    "all_items_cpi_rate": "ONS-D7G7",
    "all_items_cpi_index": "ONS-D7BT",
}


# ONS endpoint base. Matches pda-platform's URL template.
ONS_ENDPOINT_TEMPLATE = (
    "https://api.ons.gov.uk/v1/timeseries/{timeseries}/dataset/{dataset}/data"
)


@dataclass(frozen=True)
class ONSObservation:
    """One monthly observation from an ONS series."""

    indicator: str
    observation_date: date
    value: float


def fetch_ons_history(
    indicator: str,
    since: date | None = None,
    *,
    timeout: float = 30.0,
) -> list[ONSObservation]:
    """Return the full monthly history for an ONS series.

    Parameters
    ----------
    indicator:
        One of the keys in :data:`INDICATOR_MAP`.
    since:
        Optional inclusive lower bound. Observations earlier than this
        date are dropped. Useful for trimming history to the period of
        interest (the investigation's pricing base year is 2021, so
        callers typically pass ``date(2021, 1, 1)``).
    timeout:
        HTTP timeout in seconds.

    Returns
    -------
    list[ONSObservation]
        Sorted in ascending ``observation_date`` order.

    Raises
    ------
    ValueError
        If ``indicator`` is not in :data:`INDICATOR_MAP`.
    urllib.error.URLError
        If the ONS API is unreachable. Ingest rows must be
        attributable to a real fetch, so no silent fallback.
    """
    if indicator not in INDICATOR_MAP:
        raise ValueError(
            f"Unknown indicator: {indicator!r}. "
            f"Expected one of {sorted(INDICATOR_MAP)}."
        )

    dataset, timeseries, _unit, _desc = INDICATOR_MAP[indicator]
    url = ONS_ENDPOINT_TEMPLATE.format(dataset=dataset, timeseries=timeseries)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "mtd-drift-analysis/0.1"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())

    observations: list[ONSObservation] = []
    for entry in data.get("months", []):
        obs_date = _parse_ons_month(entry.get("date", ""))
        if obs_date is None:
            continue

        if since is not None and obs_date < since:
            continue

        try:
            value_float = float(entry.get("value"))
        except (TypeError, ValueError):
            continue

        observations.append(
            ONSObservation(
                indicator=indicator,
                observation_date=obs_date,
                value=value_float,
            )
        )

    observations.sort(key=lambda o: o.observation_date)
    return observations


def _parse_ons_month(ons_date: str) -> date | None:
    """Parse ONS month format (for example '2026 FEB') to a date.

    Returns the first day of the month. Returns None for malformed
    input so callers can skip rather than raise on one bad row in an
    otherwise good response.
    """
    if not ons_date:
        return None
    try:
        return datetime.strptime(ons_date.strip(), "%Y %b").date()
    except ValueError:
        return None
