"""Tests for :mod:`mtd_drift.ingest.ons_history`.

Network calls are mocked via ``urllib.request.urlopen``. Tests verify
the URL construction, response parsing (including malformed entries),
the ``since`` filter, indicator validation, and the data alignment
with pda-platform's indicator set.
"""

from __future__ import annotations

import io
import json
from datetime import date
from unittest.mock import patch

import pytest

from mtd_drift.ingest.ons_history import (
    INDICATOR_MAP,
    SERIES_CODE_BY_INDICATOR,
    ONS_ENDPOINT_TEMPLATE,
    ONSObservation,
    _parse_ons_month,
    fetch_ons_history,
)


def _mock_response(months: list[dict]) -> io.BytesIO:
    """Build a BytesIO that mimics ``urlopen`` context-manager behaviour."""
    payload = json.dumps({"months": months}).encode()

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_a):
            return False

    return _Resp(payload)


class TestFetchOnsHistory:
    def test_returns_all_months_sorted_ascending(self):
        months = [
            {"date": "2026 FEB", "value": "4.3"},
            {"date": "2025 JAN", "value": "4.1"},
            {"date": "2025 JUN", "value": "4.5"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_response(months)):
            out = fetch_ons_history("services_cpi_rate")

        assert [o.observation_date for o in out] == [
            date(2025, 1, 1),
            date(2025, 6, 1),
            date(2026, 2, 1),
        ]
        assert all(isinstance(o, ONSObservation) for o in out)
        assert all(o.indicator == "services_cpi_rate" for o in out)

    def test_since_filter_drops_earlier_months(self):
        months = [
            {"date": "2020 JAN", "value": "1.0"},
            {"date": "2021 JAN", "value": "1.2"},
            {"date": "2022 JAN", "value": "1.5"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_response(months)):
            out = fetch_ons_history("services_cpi_index", since=date(2021, 1, 1))

        dates = [o.observation_date for o in out]
        assert date(2020, 1, 1) not in dates
        assert date(2021, 1, 1) in dates
        assert date(2022, 1, 1) in dates

    def test_skips_malformed_date_rows(self):
        months = [
            {"date": "2024 JAN", "value": "1.0"},
            {"date": "gibberish", "value": "2.0"},
            {"date": "", "value": "3.0"},
            {"date": "2024 FEB", "value": "4.0"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_response(months)):
            out = fetch_ons_history("all_items_cpi_index")

        assert len(out) == 2
        assert [o.observation_date for o in out] == [
            date(2024, 1, 1),
            date(2024, 2, 1),
        ]

    def test_skips_non_numeric_value_rows(self):
        months = [
            {"date": "2024 JAN", "value": "1.0"},
            {"date": "2024 FEB", "value": None},
            {"date": "2024 MAR", "value": "not a number"},
            {"date": "2024 APR", "value": "4.0"},
        ]
        with patch("urllib.request.urlopen", return_value=_mock_response(months)):
            out = fetch_ons_history("all_items_cpi_rate")

        assert [o.value for o in out] == [1.0, 4.0]

    def test_url_includes_correct_dataset_and_timeseries(self):
        captured: dict[str, str] = {}

        def fake_urlopen(req, timeout):
            captured["url"] = req.full_url
            return _mock_response([])

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            fetch_ons_history("services_cpi_index")

        assert "MM23" in captured["url"]
        assert "D7F5" in captured["url"]
        assert captured["url"] == ONS_ENDPOINT_TEMPLATE.format(
            dataset="MM23", timeseries="D7F5"
        )

    def test_unknown_indicator_raises(self):
        with pytest.raises(ValueError, match="Unknown indicator"):
            fetch_ons_history("not_an_indicator")


class TestIndicatorMap:
    def test_covers_the_four_investigation_indicators(self):
        assert set(INDICATOR_MAP) == {
            "services_cpi_rate",
            "services_cpi_index",
            "all_items_cpi_rate",
            "all_items_cpi_index",
        }

    def test_all_indicators_have_series_code(self):
        assert set(SERIES_CODE_BY_INDICATOR) == set(INDICATOR_MAP)

    def test_series_codes_match_seed_migration(self):
        # These values are what migration 0001_mtd_2026_seed_initial_data
        # wrote into pda_shared.external_series. Divergence would break
        # the _lookup_series step in the runner.
        assert SERIES_CODE_BY_INDICATOR == {
            "services_cpi_rate": "ONS-D7NN",
            "services_cpi_index": "ONS-D7F5",
            "all_items_cpi_rate": "ONS-D7G7",
            "all_items_cpi_index": "ONS-D7BT",
        }

    def test_all_indicators_use_mm23_dataset(self):
        for key, (dataset, _ts, _unit, _desc) in INDICATOR_MAP.items():
            assert dataset == "MM23", f"{key} should be on MM23 dataset"


class TestParseOnsMonth:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("2026 FEB", date(2026, 2, 1)),
            ("2021 JAN", date(2021, 1, 1)),
            ("  2025 DEC  ", date(2025, 12, 1)),
        ],
    )
    def test_parses_valid(self, raw, expected):
        assert _parse_ons_month(raw) == expected

    @pytest.mark.parametrize(
        "raw",
        ["", "gibberish", "2024", "2024 XYZ", "FEB 2024"],
    )
    def test_returns_none_for_invalid(self, raw):
        assert _parse_ons_month(raw) is None
