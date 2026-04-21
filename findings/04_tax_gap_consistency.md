---
finding_key: tax_gap_consistency
assumption_key: self_assessment_tax_gap
methodology_section: "§6.4"
confidence: low
caveats: "§7.3 tax gap lag"
---

## Headline

{headline_line}

## Narrative

HMRC's Self Assessment tax gap assumption of 18.5% (approximately £5bn) is cited in the February 2024 TIIN (republished September 2025) as motivation for MTD for ITSA. The methodology's check compares this assumption against the most recently published estimate in HMRC's Measuring Tax Gaps (MTG) publication.

The 2025 edition of MTG, published June 2025, covers the 2023-24 tax year. Published Self Assessment tax gap figure: {comparison_value}. This compares to the 18.5% assumption at {drift_absolute:+.2f} percentage points ({drift_percent:+.2f}%).

This is a consistency check, not a drift calculation. Because MTG runs approximately two years in arrears, we cannot identify whether the tax gap has moved since the assumption was stated in September 2025; we can only report whether the two published numbers are approximately consistent.

## Methodological caveats

**§7.3 Tax gap lag.** HMRC Measuring Tax Gaps 2025 reports the 2023-24 tax year. The MTD TIIN assumption of 18.5% was stated (republished) in September 2025. There is approximately an eighteen-month gap between the tax gap measurement and the assumption statement, and a further gap between the assumption statement and this investigation. The check is of consistency, not of drift. The 2026 edition (covering 2024-25) is expected June 2026, after the intended publication window of this investigation. A follow-up check will be published when it arrives.

## Supporting drift calculation

- Drift row IDs: {supporting_drift_ids_list}

## Status

Draft. Not runnable until the non-ONS observations ingest loads the HMRC MTG 2025 Self Assessment tax gap figure into `pda_shared.external_observations`.
