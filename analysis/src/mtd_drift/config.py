"""Configuration loader for the MTD analysis package.

Credentials are read from environment variables, optionally preloaded
from a ``.env`` file at the repository root. The service role key is
never logged by this module; callers must also avoid logging
``Config.supabase_service_role_key``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Loaded credentials and endpoints for the analysis package."""

    supabase_url: str
    supabase_service_role_key: str = field(repr=False)
    pda_platform_endpoint: str | None = None

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Config":
        """Load configuration from environment variables.

        If ``env_file`` is given, load it via ``python-dotenv`` first.
        Otherwise look for ``.env`` at the repository root (three
        parents up from this file's installed location in a source
        checkout). Missing required variables raise RuntimeError with
        a clear message pointing at ``.env.example``.
        """
        if env_file is not None:
            load_dotenv(env_file)
        else:
            repo_env = _repo_root_env_file()
            if repo_env is not None and repo_env.exists():
                load_dotenv(repo_env)

        supabase_url = _require("SUPABASE_URL")
        supabase_service_role_key = _require("SUPABASE_SERVICE_ROLE_KEY")
        pda_platform_endpoint = os.environ.get("PDA_PLATFORM_ENDPOINT") or None

        return cls(
            supabase_url=supabase_url,
            supabase_service_role_key=supabase_service_role_key,
            pda_platform_endpoint=pda_platform_endpoint,
        )


def _repo_root_env_file() -> Path | None:
    """Return the expected path of ``.env`` at repo root, or None.

    Walks up from this source file looking for a directory that
    contains both ``INVESTIGATION_BRIEF.md`` and ``methodology.md``;
    that is the repository root. Returns None if not found (for
    instance, when the package is installed outside the source tree
    and the caller must provide an explicit ``env_file``).
    """
    here = Path(__file__).resolve()
    markers = {"INVESTIGATION_BRIEF.md", "methodology.md"}
    for parent in here.parents:
        if markers.issubset({p.name for p in parent.iterdir() if p.is_file()}):
            return parent / ".env"
    return None


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Required environment variable {name} is not set. "
            f"Copy .env.example to .env at the repository root and fill in the "
            f"values, or export the variable in your shell. "
            f"Never commit .env to git."
        )
    return value
