"""CLI entry point for the drift calculation runner.

Usage::

    python -m mtd_drift.drift
    python -m mtd_drift.drift --comparison-date 2026-03-01
    python -m mtd_drift.drift --verbose

Requires ``SUPABASE_URL`` and ``SUPABASE_SERVICE_ROLE_KEY`` to be set.
See ``analysis/README.md`` for setup.
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from .runner import run_drift_calculations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mtd-drift-calc",
        description=(
            "Run the five scoring steps in methodology §6 and write "
            "rows to mtd_2026.drift_calculations."
        ),
    )
    parser.add_argument(
        "--comparison-date",
        type=_parse_iso_date,
        default=None,
        help=(
            "First-of-month date to compare against the baseline. "
            "Default: two months before today (safely published ONS data)."
        ),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable INFO logging."
    )

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    results = run_drift_calculations(comparison_date=args.comparison_date)

    for r in results:
        if r.status == "executed":
            print(
                f"{r.step:<6} {r.assumption_key:<36} "
                f"drift_absolute={r.drift_absolute:>+12.2f} "
                f"drift_percent={r.drift_percent:>+7.2f}% "
                f"row_id={r.row_id}"
            )
        else:
            print(
                f"{r.step:<6} {r.assumption_key:<36} "
                f"SKIPPED: {r.skip_reason}"
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
