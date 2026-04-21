"""CLI entry point for the ONS observations ingest.

Usage::

    python -m mtd_drift.ingest
    python -m mtd_drift.ingest --since 2021-01-01
    python -m mtd_drift.ingest --indicators services_cpi_index services_cpi_rate

Requires ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` to be set,
either in the environment or in a ``.env`` file at the repository
root. See ``analysis/README.md`` for setup.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from .runner import run_ons_ingest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mtd-drift-ingest",
        description="Ingest ONS monthly series into pda_shared.external_observations.",
    )
    parser.add_argument(
        "--since",
        type=_parse_iso_date,
        default=date(2021, 1, 1),
        help="Lower bound on observation dates (YYYY-MM-DD). Default: 2021-01-01.",
    )
    parser.add_argument(
        "--indicators",
        nargs="+",
        default=None,
        help=(
            "Subset of indicators to ingest. Default: all four ONS series. "
            "Choices: services_cpi_rate services_cpi_index "
            "all_items_cpi_rate all_items_cpi_index."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable INFO-level logging.",
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    results = run_ons_ingest(since=args.since, indicators=args.indicators)

    for r in results:
        print(
            f"{r.indicator:<22} {r.series_code:<14} "
            f"fetched={r.fetched:<4} "
            f"already_present={r.already_present:<4} "
            f"inserted={r.inserted}"
        )

    return 0


def _parse_iso_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a valid ISO date (YYYY-MM-DD)"
        ) from exc


if __name__ == "__main__":
    sys.exit(main())
