# mtd-drift-analysis

Analysis package for the MTD assumption drift investigation. Case repo:
[`mtd-assumption-drift-2026`](https://github.com/antnewman/mtd-assumption-drift-2026).
Methodology: [`methodology.md`](../methodology.md).

## Scope of this package

- **Written so far (PR 2 - PR 5):** configuration loader, Supabase writer, ONS observations ingest, drift calculation runner, findings populator.
- **Follow-up:** non-ONS observations ingest (DBT BPE, HMRC MTG, OBR EFO, BoE Bank Rate) via a SQL migration with user-verified values. §6.3, §6.4, and §6.5 of the drift runner skip until those observations load, which in turn leaves findings 3, 4, and 5 as draft skips.

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
│       ├── supabase_writer.py     typed insert helpers
│       ├── ingest/
│       │   ├── __init__.py
│       │   ├── __main__.py         CLI: python -m mtd_drift.ingest
│       │   ├── ons_history.py      ONS API history fetcher
│       │   └── runner.py           orchestrator with dedup
│       ├── drift/
│       │   ├── __init__.py
│       │   ├── __main__.py         CLI: python -m mtd_drift.drift
│       │   ├── caveats.py          methodology §7 caveat flags
│       │   ├── checksum.py         SHA-256 over drift inputs
│       │   ├── reprice.py          §6.1 and §6.2 reprice formulas
│       │   └── runner.py           drift orchestrator
│       └── findings/
│           ├── __init__.py
│           ├── __main__.py         CLI: python -m mtd_drift.findings
│           └── populate.py         template parsing + insert
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_supabase_writer.py
    ├── test_ons_history.py
    ├── test_ingest_runner.py
    ├── test_drift_reprice.py
    ├── test_drift_runner.py
    └── test_findings_populate.py
```

## Running the ONS ingest

Populates `pda_shared.external_observations` with monthly values for the four ONS series used in the investigation (D7NN, D7F5, D7G7, D7BT) from 2021 onward. Idempotent; re-running inserts only new observations.

```bash
# From any directory with .env resolvable (default searches repo root):
python -m mtd_drift.ingest

# Optional: narrow to a subset of indicators or a later start date.
python -m mtd_drift.ingest \
    --since 2024-01-01 \
    --indicators services_cpi_index services_cpi_rate \
    --verbose
```

The fetch uses the ONS public timeseries API (`api.ons.gov.uk`). No API key is required. The URL pattern mirrors pda-platform's `pm_assumptions._fetch_ons`, so the provenance chain is the same.

## Running the drift calculation

Runs the five scoring steps from methodology §6 and writes one row to `mtd_2026.drift_calculations` per executed step. Steps whose required non-ONS data is not yet loaded are recorded as skipped with a clear reason.

```bash
python -m mtd_drift.drift
python -m mtd_drift.drift --comparison-date 2026-03-01 --verbose
```

Determinism: every executed row stamps an SHA-256 checksum computed over its inputs (assumption_id, series_id, baseline_value, baseline_date, comparison_date, and the index values used). Re-running with identical inputs produces identical drift values and identical checksums.

## Populating findings

```bash
python -m mtd_drift.findings
python -m mtd_drift.findings --findings-dir ../findings --verbose
```

Reads each markdown template under `findings/` (excluding `README.md`), matches each to the most recent `mtd_2026.drift_calculations` row for its `assumption_key`, and inserts a `mtd_2026.findings` row with `published = false` and `supporting_drift_ids` populated. Templates whose matching drift row does not exist are skipped with a clear reason.

Flipping a finding to `published = true` is a separate SQL step keyed by `finding_key`, taken only after reviewer sign-off is recorded in `pda_shared.reviews`.

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
