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

HMRC's average transitional cost per above-£50k-cohort business, stated at £285 in 2021 prices on the 22 February 2024 TIIN, translates to approximately £{comparison_value:.2f} when repriced to {comparison_date} using the ONS services CPI index (D7F5). This is a shift of {drift_absolute:+.2f} against the £285 baseline, or {drift_percent:+.2f}%.

This calculation applies the specific recommendation that the House of Commons Public Accounts Committee made to HMRC in its 80th report of Session 2022-23 (HC 1333, 24 November 2023): to reassess the compliance costs taking inflation into account before finalising extensions of Making Tax Digital to lower-income taxpayers. The investigation operationalises that recommendation using public data and an open-source tool.

The result is not a claim that HMRC's £285 figure was incorrect at the time it was stated. The Standard Cost Model work underpinning it is labelled as 2021 prices; repricing to a 2026 comparison point is exactly the "taking inflation into account" step the PAC asked for.

## Methodological caveats

**§7.1 services CPI vs all-items CPI.** The investigation uses ONS services CPI (D7F5) for this reprice rather than all-items CPI. Services inflation ran at 4.3% annual in February 2026, compared with 3.0% for all-items. Using the all-items index would understate the drift and would also be methodologically wrong: compliance time and software are services, not a goods-weighted basket. The investigation discloses this choice at every stage.

## Supporting drift calculation

This finding is backed by `mtd_2026.drift_calculations` row(s):

- Drift row IDs: {supporting_drift_ids_list}
- Input checksum(s) are stamped into each row's `methodology_notes` for reproducibility.

## Status

Draft. Not for publication until an independent tax-policy reviewer (per methodology §10) has signed off and a corresponding approved row exists in `pda_shared.reviews`.
