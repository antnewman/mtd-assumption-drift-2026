"""Tests for :mod:`mtd_drift.drift.reprice` and :mod:`mtd_drift.drift.checksum`."""

from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

import pytest

from mtd_drift.drift.caveats import CaveatFlag
from mtd_drift.drift.checksum import compute_input_checksum
from mtd_drift.drift.reprice import (
    reprice_aggregate_cost,
    reprice_transitional_cost,
)


def _monthly_series(
    year_start: int,
    year_end: int,
    start_value: float,
    monthly_growth_pct: float,
) -> list[tuple[date, float]]:
    """Build a synthetic monthly series for tests."""
    out: list[tuple[date, float]] = []
    value = start_value
    for year in range(year_start, year_end + 1):
        for month in range(1, 13):
            out.append((date(year, month, 1), value))
            value *= 1.0 + (monthly_growth_pct / 100.0)
    return out


class TestReprice:
    def test_2021_flat_2026_level_up(self):
        obs = _monthly_series(2021, 2026, start_value=100.0, monthly_growth_pct=0.0)
        # Inflate one specific month (2026-03) to 125 to simulate level drift.
        obs = [(d, 125.0) if d == date(2026, 3, 1) else (d, v) for d, v in obs]

        result = reprice_transitional_cost(
            assumption_id=uuid4(),
            series_id=uuid4(),
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )

        # 2021 mean = 100, 2026-03 = 125, so current = 285 * 1.25 = 356.25
        assert result.comparison_value == pytest.approx(356.25, abs=0.01)
        assert result.drift_absolute == pytest.approx(71.25, abs=0.01)
        assert result.drift_percent == pytest.approx(25.0, abs=0.01)
        assert result.index_base == pytest.approx(100.0)
        assert result.index_comparison == pytest.approx(125.0)
        assert CaveatFlag.SERVICES_CPI_CHOSEN in result.caveats

    def test_notes_mention_services_cpi_and_checksum(self):
        obs = _monthly_series(2021, 2026, start_value=120.0, monthly_growth_pct=0.25)

        result = reprice_transitional_cost(
            assumption_id=uuid4(),
            series_id=uuid4(),
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )

        assert "§6.1" in result.methodology_notes
        assert "D7F5" in result.methodology_notes
        assert "7.1:services_cpi_chosen" in result.methodology_notes
        assert result.input_checksum in result.methodology_notes
        assert len(result.input_checksum) == 64

    def test_incomplete_2021_raises(self):
        # Only 11 months of 2021.
        obs = [
            (date(2021, m, 1), 100.0) for m in range(1, 12)
        ]
        obs.append((date(2026, 3, 1), 125.0))

        with pytest.raises(ValueError, match="Need 12 monthly observations for 2021"):
            reprice_transitional_cost(
                assumption_id=uuid4(),
                series_id=uuid4(),
                baseline_value=285.0,
                baseline_date=date(2024, 2, 22),
                comparison_date=date(2026, 3, 1),
                index_observations=obs,
            )

    def test_missing_comparison_month_raises(self):
        obs = _monthly_series(2021, 2025, start_value=100.0, monthly_growth_pct=0.25)
        with pytest.raises(ValueError, match="No observation for 2026-03"):
            reprice_transitional_cost(
                assumption_id=uuid4(),
                series_id=uuid4(),
                baseline_value=285.0,
                baseline_date=date(2024, 2, 22),
                comparison_date=date(2026, 3, 1),
                index_observations=obs,
            )

    def test_aggregate_reprice_uses_same_formula(self):
        obs = _monthly_series(2021, 2026, start_value=100.0, monthly_growth_pct=0.0)
        obs = [(d, 110.0) if d == date(2026, 3, 1) else (d, v) for d, v in obs]

        result = reprice_aggregate_cost(
            assumption_id=uuid4(),
            series_id=uuid4(),
            baseline_value=561_000_000.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )
        # 561m * 1.10 = 617.1m
        assert result.comparison_value == pytest.approx(617_100_000.0, abs=1.0)
        assert result.drift_percent == pytest.approx(10.0, abs=0.01)
        assert "§6.2" in result.methodology_notes


class TestDeterminism:
    def test_same_inputs_same_checksum(self):
        aid = uuid4()
        sid = uuid4()
        obs = _monthly_series(2021, 2026, 100.0, 0.25)

        r1 = reprice_transitional_cost(
            assumption_id=aid,
            series_id=sid,
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )
        r2 = reprice_transitional_cost(
            assumption_id=aid,
            series_id=sid,
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )

        assert r1.input_checksum == r2.input_checksum
        assert r1.drift_absolute == r2.drift_absolute
        assert r1.drift_percent == r2.drift_percent

    def test_different_comparison_date_changes_checksum(self):
        aid = uuid4()
        sid = uuid4()
        obs = _monthly_series(2021, 2026, 100.0, 0.25)

        r1 = reprice_transitional_cost(
            assumption_id=aid,
            series_id=sid,
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 3, 1),
            index_observations=obs,
        )
        r2 = reprice_transitional_cost(
            assumption_id=aid,
            series_id=sid,
            baseline_value=285.0,
            baseline_date=date(2024, 2, 22),
            comparison_date=date(2026, 4, 1),
            index_observations=obs,
        )

        assert r1.input_checksum != r2.input_checksum


class TestChecksumHelper:
    def test_stable_across_extra_key_order(self):
        aid = UUID(int=1)
        c1 = compute_input_checksum(
            assumption_id=aid,
            series_id=None,
            baseline_value=100.0,
            baseline_date=date(2024, 1, 1),
            comparison_date=date(2026, 3, 1),
            extra={"a": "x", "b": "y"},
        )
        c2 = compute_input_checksum(
            assumption_id=aid,
            series_id=None,
            baseline_value=100.0,
            baseline_date=date(2024, 1, 1),
            comparison_date=date(2026, 3, 1),
            extra={"b": "y", "a": "x"},
        )
        assert c1 == c2

    def test_rounding_tolerates_float_noise(self):
        aid = UUID(int=1)
        c1 = compute_input_checksum(
            assumption_id=aid,
            series_id=None,
            baseline_value=0.1 + 0.2,  # 0.30000000000000004
            baseline_date=date(2024, 1, 1),
            comparison_date=date(2026, 3, 1),
        )
        c2 = compute_input_checksum(
            assumption_id=aid,
            series_id=None,
            baseline_value=0.3,
            baseline_date=date(2024, 1, 1),
            comparison_date=date(2026, 3, 1),
        )
        assert c1 == c2
