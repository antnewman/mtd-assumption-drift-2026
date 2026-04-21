"""CLI entry point for the findings populator.

Usage::

    python -m mtd_drift.findings
    python -m mtd_drift.findings --findings-dir ../findings --verbose

Reads markdown templates under the findings directory (defaults to
``findings/`` at the repository root), matches each to the most recent
``mtd_2026.drift_calculations`` row, and inserts
``mtd_2026.findings`` rows with ``published = false``.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .populate import populate_findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mtd-drift-findings",
        description=(
            "Populate mtd_2026.findings with draft rows generated from "
            "the markdown templates and the latest drift_calculations rows."
        ),
    )
    parser.add_argument(
        "--findings-dir",
        type=Path,
        default=None,
        help=(
            "Directory containing the findings markdown templates. "
            "Default: findings/ at the repository root."
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

    findings_dir = args.findings_dir or _default_findings_dir()
    results = populate_findings(findings_dir=findings_dir)

    for r in results:
        if r.status == "inserted":
            print(
                f"{r.finding_key:<40} INSERTED row_id={r.row_id} "
                f"drift_ids={','.join(r.drift_ids or [])}"
            )
        else:
            print(
                f"{r.finding_key:<40} SKIPPED: {r.skip_reason}"
            )

    return 0


def _default_findings_dir() -> Path:
    """Return the ``findings/`` directory at the repository root.

    Walks up from this source file looking for the repo root markers,
    the same strategy the config loader uses.
    """
    here = Path(__file__).resolve()
    markers = {"INVESTIGATION_BRIEF.md", "methodology.md"}
    for parent in here.parents:
        try:
            names = {p.name for p in parent.iterdir() if p.is_file()}
        except (FileNotFoundError, PermissionError):
            continue
        if markers.issubset(names):
            return parent / "findings"
    raise RuntimeError(
        "Could not locate findings/ directory. Pass --findings-dir."
    )


if __name__ == "__main__":
    sys.exit(main())
