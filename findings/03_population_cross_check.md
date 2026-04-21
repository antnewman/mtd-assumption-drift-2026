---
finding_key: population_cross_check_50k_cohort
assumption_key: population_50k_cohort
methodology_section: "§6.3"
confidence: low
caveats: "§7.2 BPE in-development"
---

## Headline

{headline_line}

## Narrative

HMRC's in-scope population estimate for the above-£50k cohort is 780,000 sole traders and landlords mandated into MTD for ITSA from 6 April 2026. The methodology's population cross-check compares this against the relevant subset of the DBT Business Population Estimates (BPE) 2025 publication.

The UK private-sector business population at the start of 2025 was 5.7 million, of which 4.3 million had no employees. BPE does not publish sole trader and landlord counts filtered by qualifying income threshold; the cross-check is therefore a plausibility indicator rather than a proof.

Current comparison result: {comparison_value} (compared against the £50k-cohort mandated population of 780,000). Drift: {drift_absolute:+.2f} ({drift_percent:+.2f}%).

## Methodological caveats

**§7.2 Business Population Estimates status.** BPE 2025 is classified as "official statistics in development", not as "accredited official statistics". This is a step down from the prior classification, tied to data quality concerns in the Labour Force Survey used to estimate the unregistered portion of the population. The finding discloses this status wherever the BPE figure is cited.

## Supporting drift calculation

- Drift row IDs: {supporting_drift_ids_list}

## Status

Draft. Not runnable until the non-ONS observations ingest loads BPE 2025 into `pda_shared.external_observations`. Not for publication until reviewer sign-off exists.
