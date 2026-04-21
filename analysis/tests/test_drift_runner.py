"""Tests for :mod:`mtd_drift.drift.runner`.

Patches the two Supabase loader functions directly so tests exercise
the dispatch logic without caring about the structure of supabase-py
method chains. Insert calls are captured through the mocked writer.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from mtd_drift.config import Config
from mtd_drift.drift.runner import (
    AGGREGATE_COST_KEY,
    POPULATION_KEY,
    PRIMARY_COST_KEY,
    ROI_KEY,
    TAX_GAP_KEY,
    _AssumptionRow,
    run_drift_calculations,
)
from mtd_drift.supabase_writer import SupabaseWriter


def _monthly_series(
    year_start: int,
    year_end: int,
    start_value: float,
    monthly_growth_pct: float,
) -> list[tuple[date, float]]:
    out: list[tuple[date, float]] = []
    value = start_value
    for year in range(year_start, year_end + 1):
        for month in range(1, 13):
            out.append((date(year, month, 1), value))
            value *= 1.0 + (monthly_growth_pct / 100.0)
    return out


@pytest.fixture
def writer_with_insert_stub(config: Config) -> SupabaseWriter:
    """SupabaseWriter with its client mocked to accept inserts."""
    with patch("mtd_drift.supabase_writer.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        (
            mock_client.schema.return_value.table.return_value.insert.return_value.execute.return_value.data
        ) = [{"id": "drift-row-uuid"}]
        w = SupabaseWriter(config=config)
        w._mock_client = mock_client  # type: ignore[attr-defined]
        return w


def _rigged_assumptions() -> dict[str, _AssumptionRow]:
    return {
        PRIMARY_COST_KEY: _AssumptionRow(
            id=uuid4(),
            assumption_key=PRIMARY_COST_KEY,
            value=285.0,
            baseline_date=date(2024, 2, 22),
        ),
        AGGREGATE_COST_KEY: _AssumptionRow(
            id=uuid4(),
            assumption_key=AGGREGATE_COST_KEY,
            value=561_000_000.0,
            baseline_date=date(2024, 2, 22),
        ),
    }


def _rigged_d7f5() -> tuple[UUID, list[tuple[date, float]]]:
    series_id = uuid4()
    obs = _monthly_series(2021, 2026, 100.0, 0.0)
    # Inflate 2026-03 to 125 to simulate 25% level drift.
    obs = [(d, 125.0) if d == date(2026, 3, 1) else (d, v) for d, v in obs]
    return series_id, obs


class TestRunDriftCalculations:
    def _patch_loaders(self):
        """Patch the runner's loader functions to return rigged data."""
        return (
            patch(
                "mtd_drift.drift.runner._load_active_assumptions",
                return_value=_rigged_assumptions(),
            ),
            patch(
                "mtd_drift.drift.runner._load_d7f5",
                return_value=_rigged_d7f5(),
            ),
        )

    def test_primary_and_aggregate_execute(
        self, writer_with_insert_stub: SupabaseWriter
    ):
        p1, p2 = self._patch_loaders()
        with p1, p2:
            results = run_drift_calculations(
                writer=writer_with_insert_stub,
                comparison_date=date(2026, 3, 1),
            )

        by_step = {r.step: r for r in results}

        assert by_step["§6.1"].status == "executed"
        assert by_step["§6.1"].assumption_key == PRIMARY_COST_KEY
        assert by_step["§6.1"].drift_percent == pytest.approx(25.0, abs=0.01)

        assert by_step["§6.2"].status == "executed"
        assert by_step["§6.2"].assumption_key == AGGREGATE_COST_KEY
        assert by_step["§6.2"].drift_percent == pytest.approx(25.0, abs=0.01)

    def test_non_ons_steps_skip_with_reason(
        self, writer_with_insert_stub: SupabaseWriter
    ):
        p1, p2 = self._patch_loaders()
        with p1, p2:
            results = run_drift_calculations(
                writer=writer_with_insert_stub,
                comparison_date=date(2026, 3, 1),
            )

        by_step = {r.step: r for r in results}

        assert by_step["§6.3"].status == "skipped"
        assert by_step["§6.3"].assumption_key == POPULATION_KEY
        assert "Business Population Estimates" in by_step["§6.3"].skip_reason

        assert by_step["§6.4"].status == "skipped"
        assert by_step["§6.4"].assumption_key == TAX_GAP_KEY
        assert "Measuring Tax Gaps" in by_step["§6.4"].skip_reason

        assert by_step["§6.5"].status == "skipped"
        assert by_step["§6.5"].assumption_key == ROI_KEY
        assert "OBR EFO" in by_step["§6.5"].skip_reason

    def test_returns_five_results_total(
        self, writer_with_insert_stub: SupabaseWriter
    ):
        p1, p2 = self._patch_loaders()
        with p1, p2:
            results = run_drift_calculations(
                writer=writer_with_insert_stub,
                comparison_date=date(2026, 3, 1),
            )

        assert len(results) == 5
        assert {r.step for r in results} == {
            "§6.1",
            "§6.2",
            "§6.3",
            "§6.4",
            "§6.5",
        }

    def test_primary_missing_assumption_skips_gracefully(
        self, writer_with_insert_stub: SupabaseWriter
    ):
        # Rig an empty assumptions dict (for example, seed data missing).
        with patch(
            "mtd_drift.drift.runner._load_active_assumptions",
            return_value={},
        ), patch(
            "mtd_drift.drift.runner._load_d7f5",
            return_value=_rigged_d7f5(),
        ):
            results = run_drift_calculations(
                writer=writer_with_insert_stub,
                comparison_date=date(2026, 3, 1),
            )

        by_step = {r.step: r for r in results}
        assert by_step["§6.1"].status == "skipped"
        assert "missing from mtd_2026.assumptions" in by_step["§6.1"].skip_reason

    def test_insert_receives_drift_rows(
        self, writer_with_insert_stub: SupabaseWriter
    ):
        """§6.1 and §6.2 should each trigger one batch-insert call."""
        p1, p2 = self._patch_loaders()
        with p1, p2:
            run_drift_calculations(
                writer=writer_with_insert_stub,
                comparison_date=date(2026, 3, 1),
            )

        # The insert() path is hit twice (once per executed step).
        insert_mock = (
            writer_with_insert_stub._mock_client.schema.return_value
            .table.return_value.insert
        )
        assert insert_mock.call_count == 2

        # Check one of the payloads has the expected shape.
        call_payload = insert_mock.call_args_list[0].args[0]
        assert "drift_absolute" in call_payload
        assert "drift_percent" in call_payload
        assert "methodology_notes" in call_payload
        assert "§6.1" in call_payload["methodology_notes"] or "§6.2" in call_payload["methodology_notes"]
