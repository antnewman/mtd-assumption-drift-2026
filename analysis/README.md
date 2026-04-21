# mtd-drift-analysis

Analysis package for the MTD assumption drift investigation. Case repo:
[`mtd-assumption-drift-2026`](https://github.com/antnewman/mtd-assumption-drift-2026).
Methodology: [`methodology.md`](../methodology.md).

## Scope of this package

- **Written so far (PR 2):** configuration loader and Supabase writer skeleton.
- **To come:** ONS ingest adapter (PR 3), drift calculation runner (PR 4), findings populator (PR 5).

## Setup

Requires Python 3.11 or later.

From the repository root:

```bash
cp .env.example .env
# Fill in SUPABASE_SERVICE_ROLE_KEY from the Supabase dashboard at
# https://supabase.com/dashboard/project/bulheatuxvktopxrwbvs (Settings > API).
# Never commit .env; it is gitignored.

cd analysis
pip install -e ".[dev]"
```

## Run tests

```bash
cd analysis
pytest
```

The tests mock the Supabase client and run without network access. They do not require valid credentials.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL. For `pda-investigations`: `https://bulheatuxvktopxrwbvs.supabase.co`. |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes | Service role key for writes. Never commit. Rotate if exposed. |
| `PDA_PLATFORM_ENDPOINT` | No | Hosted PDA Platform MCP endpoint. Leave blank to use a local in-process install, which is the default recommended for reproducibility. |

## Key rotation

Service role keys are rotated from the Supabase dashboard: Settings > API > regenerate JWT secret. After rotation:

1. Generate the new key in the dashboard.
2. Update `.env` on every developer machine and CI target.
3. Confirm the previous key has been invalidated.

Never paste the service role key into issue trackers, chat transcripts, or PR descriptions. If exposure occurs, rotate immediately.

## Package layout

```
analysis/
├── pyproject.toml
├── README.md
├── src/
│   └── mtd_drift/
│       ├── __init__.py
│       ├── config.py              loads .env and environment
│       └── supabase_writer.py     typed insert helpers
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_supabase_writer.py
```

## What the Supabase writer does

Three typed insert helpers, one per append-only table:

| Helper | Target table | Schema |
|---|---|---|
| `insert_external_observation` | `external_observations` | `pda_shared` |
| `insert_drift_calculation` | `drift_calculations` | `mtd_2026` |
| `insert_finding` | `findings` | `mtd_2026` |

Schema changes are not performed by this module. Schema lives in `supabase/migrations/` and is applied via the Supabase MCP `apply_migration` tool, not via `SupabaseWriter`.

The `SupabaseWriter` object never logs its service role key and redacts the key from its `repr`. Callers should avoid logging the `Config` object or its fields.

## Related

- [`INVESTIGATION_BRIEF.md`](../INVESTIGATION_BRIEF.md): the case framing.
- [`methodology.md`](../methodology.md): public methodology, especially §6 (scoring), §7 (caveats), §10 (review gate).
- [`supabase/migrations/`](../supabase/migrations/): schema and seed SQL.
- [PDA Platform](https://github.com/antnewman/pda-platform): the analysis tool.
