"""Shared pytest fixtures for MTD drift analysis tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from mtd_drift.config import Config
from mtd_drift.supabase_writer import SupabaseWriter


@pytest.fixture
def config() -> Config:
    """A Config instance populated with test credentials.

    Never used against a real Supabase project; the client is always
    mocked in ``writer`` below.
    """
    return Config(
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="test-service-role-key-do-not-log",
        pda_platform_endpoint=None,
    )


@pytest.fixture
def writer(config: Config) -> SupabaseWriter:
    """A SupabaseWriter with its underlying client mocked.

    The mock is attached as ``writer._mock_client`` so tests can
    inspect call arguments without reaching for internal attributes in
    multiple places.
    """
    with patch("mtd_drift.supabase_writer.create_client") as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        mock_client.schema.return_value.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "generated-uuid"}
        ]
        w = SupabaseWriter(config=config)
        w._mock_client = mock_client  # type: ignore[attr-defined]
        return w
