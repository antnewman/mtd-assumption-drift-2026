"""Tests for :mod:`mtd_drift.findings.populate`."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from mtd_drift.config import Config
from mtd_drift.findings.populate import (
    FindingTemplate,
    _classify,
    _parse_simple_yaml,
    parse_finding_file,
    populate_findings,
)
from mtd_drift.supabase_writer import SupabaseWriter


@pytest.fixture
def findings_dir(tmp_path: Path) -> Path:
    """Temp directory with one valid finding template and a README."""
    (tmp_path / "README.md").write_text(encoding="utf-8", data="# Findings README (not a template)\n")
    (tmp_path / "01_test.md").write_text(encoding="utf-8", data=
        textwrap.dedent(
            """\
            ---
            finding_key: test_finding
            assumption_key: transitional_cost_50k_cohort
            methodology_section: "§6.1"
            confidence: medium
            caveats: "§7.1 services CPI chosen"
            ---

            ## Headline

            {headline_line}

            ## Body

            Baseline £{baseline_value:.2f} drifted to £{comparison_value:.2f}
            at {comparison_date} ({drift_percent:+.2f}%).
            """
        )
    )
    return tmp_path


@pytest.fixture
def writer_with_stub(config: Config) -> SupabaseWriter:
    """SupabaseWriter with a mock client; individual tests rig responses."""
    with patch("mtd_drift.supabase_writer.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        w = SupabaseWriter(config=config)
        w._mock_client = mock_client  # type: ignore[attr-defined]
        return w


def _rig_insert(writer: SupabaseWriter, row_id: str = "finding-uuid") -> None:
    (
        writer._mock_client.schema.return_value
        .table.return_value
        .insert.return_value
        .execute.return_value.data
    ) = [{"id": row_id}]


class TestParseFindingFile:
    def test_parses_valid(self, findings_dir: Path):
        tpl = parse_finding_file(findings_dir / "01_test.md")
        assert tpl.finding_key == "test_finding"
        assert tpl.assumption_key == "transitional_cost_50k_cohort"
        assert tpl.methodology_section == "§6.1"
        assert tpl.confidence == "medium"
        assert tpl.caveats == "§7.1 services CPI chosen"
        assert "{baseline_value" in tpl.body_template

    def test_missing_front_matter_raises(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text(encoding="utf-8", data="no front matter here\n")
        with pytest.raises(ValueError, match="YAML front matter"):
            parse_finding_file(p)

    def test_missing_required_key_raises(self, tmp_path: Path):
        p = tmp_path / "bad.md"
        p.write_text(encoding="utf-8", data=
            textwrap.dedent(
                """\
                ---
                finding_key: x
                ---

                body
                """
            )
        )
        with pytest.raises(ValueError, match="missing required keys"):
            parse_finding_file(p)


class TestClassify:
    @pytest.mark.parametrize(
        "pct,expected_magnitude,expected_direction",
        [
            (0.5, "small", "positive"),
            (-0.5, "small", "negative"),
            (7.0, "moderate", "positive"),
            (-10.0, "moderate", "negative"),
            (25.0, "substantial", "positive"),
            (-30.0, "substantial", "negative"),
        ],
    )
    def test_classify(self, pct, expected_magnitude, expected_direction):
        magnitude, direction = _classify(pct)
        assert magnitude == expected_magnitude
        assert direction == expected_direction


class TestParseSimpleYaml:
    def test_strips_quotes(self):
        parsed = _parse_simple_yaml('key: "quoted value"')
        assert parsed == {"key": "quoted value"}

    def test_skips_comments_and_blanks(self):
        parsed = _parse_simple_yaml(
            "# comment\n\nkey: value\n   \n"
        )
        assert parsed == {"key": "value"}

    def test_malformed_raises(self):
        with pytest.raises(ValueError, match="Malformed"):
            _parse_simple_yaml("no_colon_here")


class TestPopulateFindings:
    def _patch_lookups(self, drift_row: dict | None):
        """Patch _latest_assumption and _latest_drift_row."""
        assumption_id = str(uuid4())
        assumption = {
            "id": assumption_id,
            "assumption_key": "transitional_cost_50k_cohort",
            "baseline_date": "2024-02-22",
        }
        return (
            patch(
                "mtd_drift.findings.populate._latest_assumption",
                return_value=assumption,
            ),
            patch(
                "mtd_drift.findings.populate._latest_drift_row",
                return_value=drift_row,
            ),
        )

    def test_inserts_finding_when_drift_row_present(
        self, findings_dir: Path, writer_with_stub: SupabaseWriter
    ):
        drift_row = {
            "id": str(uuid4()),
            "assumption_id": str(uuid4()),
            "series_id": str(uuid4()),
            "baseline_value": 285.0,
            "baseline_date": "2024-02-22",
            "comparison_value": 356.25,
            "comparison_date": "2026-03-01",
            "drift_absolute": 71.25,
            "drift_percent": 25.0,
            "methodology_notes": "§6.1 services CPI reprice via D7F5",
            "confidence": "medium",
        }
        _rig_insert(writer_with_stub)

        p1, p2 = self._patch_lookups(drift_row)
        with p1, p2:
            results = populate_findings(
                findings_dir=findings_dir,
                writer=writer_with_stub,
            )

        assert len(results) == 1
        r = results[0]
        assert r.status == "inserted"
        assert r.finding_key == "test_finding"
        assert r.drift_ids == [drift_row["id"]]

    def test_skips_when_no_drift_row(
        self, findings_dir: Path, writer_with_stub: SupabaseWriter
    ):
        p1, p2 = self._patch_lookups(None)
        with p1, p2:
            results = populate_findings(
                findings_dir=findings_dir,
                writer=writer_with_stub,
            )

        assert len(results) == 1
        r = results[0]
        assert r.status == "skipped"
        assert "No drift_calculations row" in r.skip_reason

    def test_skips_when_no_assumption_row(
        self, findings_dir: Path, writer_with_stub: SupabaseWriter
    ):
        with patch(
            "mtd_drift.findings.populate._latest_assumption",
            return_value=None,
        ):
            results = populate_findings(
                findings_dir=findings_dir,
                writer=writer_with_stub,
            )

        assert len(results) == 1
        assert results[0].status == "skipped"
        assert "No active assumption row" in results[0].skip_reason

    def test_formatted_narrative_contains_drift_values(
        self, findings_dir: Path, writer_with_stub: SupabaseWriter
    ):
        drift_row = {
            "id": str(uuid4()),
            "assumption_id": str(uuid4()),
            "series_id": str(uuid4()),
            "baseline_value": 285.0,
            "baseline_date": "2024-02-22",
            "comparison_value": 356.25,
            "comparison_date": "2026-03-01",
            "drift_absolute": 71.25,
            "drift_percent": 25.0,
            "methodology_notes": "§6.1 services CPI reprice",
            "confidence": "medium",
        }
        _rig_insert(writer_with_stub)

        captured_payload: dict = {}

        def capture_insert_finding(finding):
            captured_payload["finding"] = finding
            return {"id": "finding-uuid"}

        writer_with_stub.insert_finding = capture_insert_finding  # type: ignore[method-assign]

        p1, p2 = self._patch_lookups(drift_row)
        with p1, p2:
            populate_findings(
                findings_dir=findings_dir,
                writer=writer_with_stub,
            )

        finding = captured_payload["finding"]
        assert "285.00" in finding.narrative
        assert "356.25" in finding.narrative
        assert "2026-03-01" in finding.narrative
        assert "+25.00%" in finding.narrative
        assert finding.published is False
        assert finding.magnitude == "substantial"
        assert finding.direction == "positive"

    def test_readme_is_not_treated_as_template(
        self, findings_dir: Path, writer_with_stub: SupabaseWriter
    ):
        # README.md exists in findings_dir but must be skipped.
        p1, p2 = self._patch_lookups(None)
        with p1, p2:
            results = populate_findings(
                findings_dir=findings_dir,
                writer=writer_with_stub,
            )
        # Only the 01_test.md template, not the README.
        assert len(results) == 1
        assert results[0].finding_key == "test_finding"
