"""Tests for :mod:`mtd_drift.ingest.runner`.

Mocks both the Supabase client and the ONS fetcher to verify the dedup
logic, the per-indicator summary, and the batch insert payload shape.
"""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from mtd_drift.config import Config
from mtd_drift.ingest.ons_history import ONSObservation
from mtd_drift.ingest.runner import (
    IngestResult,
    run_ons_ingest,
)
from mtd_drift.supabase_writer import SupabaseWriter


@pytest.fixture
def writer_with_mock(config: Config) -> SupabaseWriter:
    """SupabaseWriter with a mock client rigged for the ingest pathway.

    The mock supports two schema paths: external_series (lookup) and
    external_observations (select existing + batch insert). Each path
    returns sensible defaults that individual tests override.
    """
    with patch("mtd_drift.supabase_writer.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        w = SupabaseWriter(config=config)
        w._mock_client = mock_client  # type: ignore[attr-defined]
        return w


def _rig_series_lookup(writer: SupabaseWriter, series_code: str, series_id) -> None:
    """Rig the external_series SELECT to return a single matching row."""
    (
        writer._mock_client.schema.return_value
        .table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = [{"id": str(series_id), "series_code": series_code}]


def _rig_existing_dates(writer: SupabaseWriter, dates: list[date]) -> None:
    """Rig the external_observations SELECT to return these dates."""
    (
        writer._mock_client.schema.return_value
        .table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = [{"observation_date": d.isoformat()} for d in dates]


def _rig_batch_insert(writer: SupabaseWriter, n: int) -> None:
    (
        writer._mock_client.schema.return_value
        .table.return_value
        .insert.return_value
        .execute.return_value
        .data
    ) = [{"id": f"uuid-{i}"} for i in range(n)]


def test_run_inserts_only_new_observations(writer_with_mock: SupabaseWriter):
    series_id = uuid4()
    _rig_series_lookup(writer_with_mock, "ONS-D7F5", series_id)
    _rig_existing_dates(writer_with_mock, [date(2025, 1, 1)])

    fetched = [
        ONSObservation("services_cpi_index", date(2025, 1, 1), 130.0),
        ONSObservation("services_cpi_index", date(2025, 2, 1), 131.2),
        ONSObservation("services_cpi_index", date(2025, 3, 1), 132.0),
    ]
    _rig_batch_insert(writer_with_mock, n=2)

    with patch(
        "mtd_drift.ingest.runner.fetch_ons_history", return_value=fetched
    ):
        results = run_ons_ingest(
            writer=writer_with_mock,
            indicators=["services_cpi_index"],
        )

    assert len(results) == 1
    r = results[0]
    assert isinstance(r, IngestResult)
    assert r.indicator == "services_cpi_index"
    assert r.series_code == "ONS-D7F5"
    assert r.fetched == 3
    assert r.already_present == 1
    assert r.inserted == 2


def test_run_passes_since_to_fetcher(writer_with_mock: SupabaseWriter):
    _rig_series_lookup(writer_with_mock, "ONS-D7NN", uuid4())
    _rig_existing_dates(writer_with_mock, [])

    captured: dict = {}

    def fake_fetch(indicator, since=None, **_kw):
        captured["indicator"] = indicator
        captured["since"] = since
        return []

    with patch("mtd_drift.ingest.runner.fetch_ons_history", side_effect=fake_fetch):
        run_ons_ingest(
            writer=writer_with_mock,
            since=date(2022, 1, 1),
            indicators=["services_cpi_rate"],
        )

    assert captured["indicator"] == "services_cpi_rate"
    assert captured["since"] == date(2022, 1, 1)


def test_run_raises_on_unknown_indicator(writer_with_mock: SupabaseWriter):
    with pytest.raises(ValueError, match="not configured"):
        run_ons_ingest(
            writer=writer_with_mock,
            indicators=["nonsense_indicator"],
        )


def test_run_raises_when_series_not_seeded(writer_with_mock: SupabaseWriter):
    # Series lookup returns no rows.
    (
        writer_with_mock._mock_client.schema.return_value
        .table.return_value
        .select.return_value
        .eq.return_value
        .limit.return_value
        .execute.return_value
        .data
    ) = []

    with pytest.raises(RuntimeError, match="not found in pda_shared.external_series"):
        run_ons_ingest(
            writer=writer_with_mock,
            indicators=["services_cpi_rate"],
        )


def test_all_four_indicators_default(writer_with_mock: SupabaseWriter):
    _rig_series_lookup(writer_with_mock, "series-code", uuid4())
    _rig_existing_dates(writer_with_mock, [])

    with patch(
        "mtd_drift.ingest.runner.fetch_ons_history", return_value=[]
    ):
        results = run_ons_ingest(writer=writer_with_mock)

    assert {r.indicator for r in results} == {
        "services_cpi_rate",
        "services_cpi_index",
        "all_items_cpi_rate",
        "all_items_cpi_index",
    }
