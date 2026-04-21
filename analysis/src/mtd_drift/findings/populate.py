"""Findings populator.

Reads markdown templates under ``findings/``, matches each template to
the most recent ``mtd_2026.drift_calculations`` row for its
``assumption_key``, formats the narrative with the drift row's values,
and inserts a ``mtd_2026.findings`` row with ``published = false``.

Templates whose drift row does not yet exist are skipped with a clear
reason.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from uuid import UUID

from ..config import Config
from ..supabase_writer import Finding, SupabaseWriter

logger = logging.getLogger(__name__)


# Regex for YAML-style front matter at the start of a markdown file.
# Opening fence: three dashes on their own line.
# Closing fence: three dashes on their own line.
_FRONT_MATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)\Z",
    re.DOTALL,
)


@dataclass(frozen=True)
class FindingTemplate:
    """A parsed findings markdown file.

    ``body_template`` is the body with placeholders that the populator
    substitutes when a matching drift row is found.
    """

    path: Path
    finding_key: str
    assumption_key: str
    methodology_section: str
    confidence: str
    caveats: str
    body_template: str


@dataclass(frozen=True)
class PopulateResult:
    """Outcome for one finding template."""

    finding_key: str
    status: str  # "inserted" or "skipped"
    row_id: str | None = None
    drift_ids: list[str] = None  # type: ignore[assignment]
    skip_reason: str | None = None


def parse_finding_file(path: Path) -> FindingTemplate:
    """Parse a findings markdown file into a :class:`FindingTemplate`."""
    raw = path.read_text(encoding="utf-8")
    match = _FRONT_MATTER_RE.match(raw)
    if match is None:
        raise ValueError(
            f"{path} does not start with YAML front matter "
            f"(expected '---' fences)."
        )

    front_matter = _parse_simple_yaml(match.group("fm"))
    body = match.group("body")

    required = {
        "finding_key",
        "assumption_key",
        "methodology_section",
        "confidence",
        "caveats",
    }
    missing = required - front_matter.keys()
    if missing:
        raise ValueError(
            f"{path} front matter is missing required keys: {sorted(missing)}"
        )

    return FindingTemplate(
        path=path,
        finding_key=front_matter["finding_key"],
        assumption_key=front_matter["assumption_key"],
        methodology_section=front_matter["methodology_section"],
        confidence=front_matter["confidence"],
        caveats=front_matter["caveats"],
        body_template=body,
    )


def populate_findings(
    *,
    findings_dir: Path,
    writer: SupabaseWriter | None = None,
    config: Config | None = None,
) -> list[PopulateResult]:
    """Read every markdown template in ``findings_dir`` and populate.

    Does not republish or update existing rows; every call appends new
    draft rows with ``published = false``. Rerunning the populator is
    therefore safe but will accumulate draft rows over time. Typical
    use: run once after a drift calculation, review the inserted
    drafts, flip to published via a short SQL update keyed by
    ``finding_key`` after reviewer sign-off.
    """
    if writer is None:
        writer = SupabaseWriter(config=config)

    templates = _load_templates(findings_dir)
    results: list[PopulateResult] = []

    for template in templates:
        assumption = _latest_assumption(writer, template.assumption_key)
        if assumption is None:
            results.append(
                PopulateResult(
                    finding_key=template.finding_key,
                    status="skipped",
                    skip_reason=(
                        f"No active assumption row for "
                        f"{template.assumption_key!r} in mtd_2026.assumptions."
                    ),
                )
            )
            continue

        drift_row = _latest_drift_row(
            writer, assumption["id"], template.methodology_section
        )
        if drift_row is None:
            results.append(
                PopulateResult(
                    finding_key=template.finding_key,
                    status="skipped",
                    skip_reason=(
                        f"No drift_calculations row for assumption_key "
                        f"{template.assumption_key!r} and section "
                        f"{template.methodology_section!r}. Run "
                        f"`python -m mtd_drift.drift` first, or wait for "
                        f"non-ONS observations if this step needs them."
                    ),
                )
            )
            continue

        narrative = _format_narrative(template, drift_row)
        magnitude, direction = _classify(drift_row["drift_percent"])

        finding = Finding(
            finding_key=template.finding_key,
            headline=_headline(template, drift_row, direction, magnitude),
            narrative=narrative,
            magnitude=magnitude,
            direction=direction,
            confidence=template.confidence,
            caveats=template.caveats,
            supporting_drift_ids=[UUID(drift_row["id"])],
            published=False,
        )

        row = writer.insert_finding(finding)
        results.append(
            PopulateResult(
                finding_key=template.finding_key,
                status="inserted",
                row_id=row.get("id"),
                drift_ids=[drift_row["id"]],
            )
        )

    return results


def _load_templates(findings_dir: Path) -> list[FindingTemplate]:
    paths = sorted(
        p
        for p in findings_dir.iterdir()
        if p.is_file()
        and p.suffix == ".md"
        and p.name != "README.md"
    )
    return [parse_finding_file(p) for p in paths]


def _latest_assumption(
    writer: SupabaseWriter, assumption_key: str
) -> dict[str, Any] | None:
    resp = (
        writer._client.schema("mtd_2026")
        .table("assumptions")
        .select("id,assumption_key,baseline_date")
        .eq("assumption_key", assumption_key)
        .eq("is_superseded", False)
        .order("baseline_date", desc=True)
        .limit(1)
        .execute()
    )
    data = getattr(resp, "data", None) or []
    return data[0] if data else None


def _latest_drift_row(
    writer: SupabaseWriter,
    assumption_id: str,
    methodology_section: str,
) -> dict[str, Any] | None:
    resp = (
        writer._client.schema("mtd_2026")
        .table("drift_calculations")
        .select(
            "id,assumption_id,series_id,baseline_value,baseline_date,"
            "comparison_value,comparison_date,drift_absolute,drift_percent,"
            "methodology_notes,confidence,run_at"
        )
        .eq("assumption_id", str(assumption_id))
        .order("run_at", desc=True)
        .execute()
    )
    data = getattr(resp, "data", None) or []
    # Filter for rows whose methodology_notes mentions the expected
    # section. The runner always stamps the section marker at the
    # start of methodology_notes.
    for row in data:
        notes = row.get("methodology_notes", "") or ""
        if methodology_section in notes:
            return row
    return None


def _format_narrative(
    template: FindingTemplate, drift_row: dict[str, Any]
) -> str:
    cmp_date = _as_date(drift_row["comparison_date"]).isoformat()
    values: dict[str, Any] = {
        "comparison_value": float(drift_row["comparison_value"]),
        "comparison_date": cmp_date,
        "drift_absolute": float(drift_row["drift_absolute"]),
        "drift_percent": float(drift_row["drift_percent"]),
        "baseline_value": float(drift_row["baseline_value"]),
        "headline_line": "",  # filled in separately
        "supporting_drift_ids_list": drift_row["id"],
    }
    # Placeholder for headline; replaced after classify().
    values["headline_line"] = _headline_text(drift_row)
    return template.body_template.format_map(_SafeFormatDict(values))


def _headline(
    template: FindingTemplate,
    drift_row: dict[str, Any],
    direction: str,
    magnitude: str,
) -> str:
    percent = float(drift_row["drift_percent"])
    return (
        f"{template.methodology_section}: {magnitude} {direction} drift of "
        f"{percent:+.2f}% against the {template.assumption_key} baseline."
    )


def _headline_text(drift_row: dict[str, Any]) -> str:
    pct = float(drift_row["drift_percent"])
    return f"Drift of {pct:+.2f}% against the HMRC baseline as stated in the TIIN."


def _classify(drift_percent: float) -> tuple[str, str]:
    direction = "positive" if drift_percent >= 0 else "negative"
    abs_pct = abs(drift_percent)
    if abs_pct < 5.0:
        magnitude = "small"
    elif abs_pct < 15.0:
        magnitude = "moderate"
    else:
        magnitude = "substantial"
    return magnitude, direction


def _as_date(value: Any) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


class _SafeFormatDict(dict):
    """str.format_map dict that leaves unknown placeholders untouched."""

    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def _parse_simple_yaml(text: str) -> dict[str, str]:
    """Minimal YAML parser for ``key: value`` pairs with optional quotes.

    The finding front matter uses only flat key/value pairs, so a full
    YAML dependency is unnecessary. Rejects indented structures.
    """
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"Malformed front-matter line: {line!r}")
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        out[key] = value
    return out
