# Findings

This directory holds the narrative findings of the MTD assumption drift investigation. Each finding is a markdown file with a YAML front-matter header.

## Status

No finding is published on the public Tortoise website or in Zenodo until both of the following have happened:

1. An independent domain reviewer (per methodology §10) has completed the review, and
2. An approved review record exists in `pda_shared.reviews` with `consent_to_name` made explicit.

The flip from draft to published is a separate, explicit step executed by a short SQL update per `finding_key`. Until then, every row in `mtd_2026.findings` has `published = false`.

## File format

Each markdown file uses YAML front-matter plus a body. The body is a Python `str.format_map(...)` template: placeholders in `{curly_braces}` are substituted by the populator with values pulled from the most recent matching `mtd_2026.drift_calculations` row.

```markdown
---
finding_key: transitional_cost_drift_50k_cohort
assumption_key: transitional_cost_50k_cohort
methodology_section: "§6.1"
confidence: medium
caveats: "§7.1 services CPI chosen"
---

## Headline

{headline_line}

## Narrative

When the ONS services CPI index (D7F5) is applied to the £285 baseline
from 2021 prices to {comparison_date}, the current-price equivalent is
£{comparison_value:.2f}. Drift versus the £285 baseline is
{drift_absolute:+.2f} (that is, {drift_percent:+.2f}%).

[...]
```

## Finding index

| # | File | Methodology step | Populates from |
|---|---|---|---|
| 1 | [`01_transitional_cost_drift_50k_cohort.md`](01_transitional_cost_drift_50k_cohort.md) | §6.1 | `transitional_cost_50k_cohort` drift rows |
| 2 | [`02_transitional_cost_drift_aggregate.md`](02_transitional_cost_drift_aggregate.md) | §6.2 | `transitional_cost_total_30k_plus` drift rows |
| 3 | [`03_population_cross_check.md`](03_population_cross_check.md) | §6.3 | `population_50k_cohort` drift rows (pending non-ONS ingest) |
| 4 | [`04_tax_gap_consistency.md`](04_tax_gap_consistency.md) | §6.4 | `self_assessment_tax_gap` drift rows (pending) |
| 5 | [`05_roi_sensitivity.md`](05_roi_sensitivity.md) | §6.5 | `programme_roi` drift rows (pending) |

## Populating findings

```bash
python -m mtd_drift.findings
python -m mtd_drift.findings --verbose
```

The populator reads each markdown file, looks up the most recent matching drift row by `assumption_key`, formats the narrative with the drift values, and inserts a row into `mtd_2026.findings` with `published = false` and `supporting_drift_ids` populated. Files whose matching drift row does not exist (typically because the non-ONS observations have not been ingested yet) are skipped with a clear reason.

## Caveats

Every published finding carries its methodology caveats in full. Caveats are defined in methodology §7:

- §7.1 Services CPI vs all-items CPI
- §7.2 Business Population Estimates status
- §7.3 Tax gap lag

Each finding file's front-matter declares the caveats that apply to it.
