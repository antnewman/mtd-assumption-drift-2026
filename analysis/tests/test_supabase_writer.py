"""Tests for :class:`mtd_drift.supabase_writer.SupabaseWriter`.

Verifies the shape of the payload sent to Supabase for each of the
three insert helpers, the schema and table targeting, and that the
service role key is not exposed via logs or ``repr``.
"""

from __future__ import annotations

import logging
from datetime import date
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from mtd_drift.config import Config
from mtd_drift.supabase_writer import (
    DriftCalculation,
    ExternalObservation,
    Finding,
    SupabaseWriter,
    _first_row,
)


class TestInsertExternalObservation:
    def test_targets_pda_shared_external_observations(self, writer):
        obs = ExternalObservation(
            series_id=uuid4(),
            observation_date=date(2026, 2, 1),
            value=4.3,
        )
        writer.insert_external_observation(obs)

        writer._mock_client.schema.assert_called_with("pda_shared")
        writer._mock_client.schema.return_value.table.assert_called_with(
            "external_observations"
        )

    def test_payload_shape(self, writer):
        series_id = uuid4()
        obs = ExternalObservation(
            series_id=series_id,
            observation_date=date(2026, 2, 1),
            value=4.3,
            notes="ONS D7NN services CPI annual rate, February 2026",
        )
        writer.insert_external_observation(obs)

        call = writer._mock_client.schema.return_value.table.return_value.insert.call_args
        payload = call.args[0]
        assert payload["series_id"] == str(series_id)
        assert payload["observation_date"] == "2026-02-01"
        assert payload["value"] == pytest.approx(4.3)
        assert payload["notes"] == "ONS D7NN services CPI annual rate, February 2026"

    def test_notes_is_optional(self, writer):
        obs = ExternalObservation(
            series_id=uuid4(),
            observation_date=date(2026, 2, 1),
            value=4.3,
        )
        writer.insert_external_observation(obs)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["notes"] is None


class TestInsertDriftCalculation:
    def test_targets_mtd_2026_drift_calculations(self, writer):
        calc = _sample_drift()
        writer.insert_drift_calculation(calc)

        writer._mock_client.schema.assert_called_with("mtd_2026")
        writer._mock_client.schema.return_value.table.assert_called_with(
            "drift_calculations"
        )

    def test_payload_shape(self, writer):
        calc = _sample_drift()
        writer.insert_drift_calculation(calc)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["assumption_id"] == str(calc.assumption_id)
        assert payload["series_id"] == str(calc.series_id)
        assert payload["baseline_value"] == pytest.approx(285.0)
        assert payload["baseline_date"] == "2024-02-22"
        assert payload["comparison_value"] == pytest.approx(325.6)
        assert payload["comparison_date"] == "2026-03-31"
        assert payload["drift_absolute"] == pytest.approx(40.6)
        assert payload["drift_percent"] == pytest.approx(14.25)
        assert payload["methodology_notes"].startswith("§6.1")
        assert payload["confidence"] == "medium"

    def test_series_id_may_be_null(self, writer):
        calc = _sample_drift(series_id=None)
        writer.insert_drift_calculation(calc)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["series_id"] is None


class TestInsertFinding:
    def test_targets_mtd_2026_findings(self, writer):
        finding = _sample_finding()
        writer.insert_finding(finding)

        writer._mock_client.schema.assert_called_with("mtd_2026")
        writer._mock_client.schema.return_value.table.assert_called_with("findings")

    def test_default_published_false(self, writer):
        finding = _sample_finding()
        writer.insert_finding(finding)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["published"] is False

    def test_supporting_drift_ids_serialised_as_strings(self, writer):
        d1, d2 = uuid4(), uuid4()
        finding = _sample_finding(supporting_drift_ids=[d1, d2])
        writer.insert_finding(finding)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["supporting_drift_ids"] == [str(d1), str(d2)]

    def test_supporting_drift_ids_none_passes_through(self, writer):
        finding = _sample_finding(supporting_drift_ids=None)
        writer.insert_finding(finding)

        payload = (
            writer._mock_client.schema.return_value.table.return_value.insert.call_args.args[0]
        )
        assert payload["supporting_drift_ids"] is None


class TestServiceRoleKeyIsNotExposed:
    def test_repr_redacts_key(self, config):
        with patch("mtd_drift.supabase_writer.create_client") as mock_create:
            mock_create.return_value = MagicMock()
            w = SupabaseWriter(config=config)

        text = repr(w)
        assert config.supabase_service_role_key not in text
        assert "<redacted>" in text

    def test_construction_does_not_log_key(self, config, caplog):
        with caplog.at_level(logging.DEBUG):
            with patch("mtd_drift.supabase_writer.create_client") as mock_create:
                mock_create.return_value = MagicMock()
                SupabaseWriter(config=config)

        for record in caplog.records:
            assert config.supabase_service_role_key not in record.getMessage()


class TestFirstRowHelper:
    def test_returns_first_row(self):
        resp = MagicMock(data=[{"id": "abc"}, {"id": "def"}])
        assert _first_row(resp) == {"id": "abc"}

    def test_empty_response_raises(self):
        resp = MagicMock(data=[])
        with pytest.raises(RuntimeError, match="returned no rows"):
            _first_row(resp)

    def test_missing_data_attribute_raises(self):
        resp = object()  # no data attribute
        with pytest.raises(RuntimeError, match="returned no rows"):
            _first_row(resp)


def _sample_drift(series_id=...) -> DriftCalculation:
    return DriftCalculation(
        assumption_id=uuid4(),
        series_id=uuid4() if series_id is ... else series_id,
        baseline_value=285.0,
        baseline_date=date(2024, 2, 22),
        comparison_value=325.6,
        comparison_date=date(2026, 3, 31),
        drift_absolute=40.6,
        drift_percent=14.25,
        methodology_notes=(
            "§6.1 services CPI reprice (D7F5 2024-02 → 2026-03). "
            "Caveat flags: 7.1 (services CPI chosen)."
        ),
        confidence="medium",
    )


def _sample_finding(supporting_drift_ids=...) -> Finding:
    return Finding(
        finding_key="transitional_cost_drift",
        headline="Per-business transitional cost has drifted",
        narrative="Narrative body",
        magnitude="moderate",
        direction="positive",
        confidence="medium",
        caveats="§7.1 (services CPI chosen)",
        supporting_drift_ids=(
            [uuid4()] if supporting_drift_ids is ... else supporting_drift_ids
        ),
    )
