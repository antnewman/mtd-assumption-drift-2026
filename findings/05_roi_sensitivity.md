---
finding_key: roi_sensitivity
assumption_key: programme_roi
methodology_section: "§6.5"
confidence: low
caveats: "§7.1 services CPI chosen"
---

## Headline

{headline_line}

## Narrative

The June 2025 HMRC Accounting Officer Assessment of the MTD Programme reports a programme return on investment of 3.8:1 and a benefit-cost ratio (BCR) of 1.3:1. These figures were revised from the April 2024 AOA (ROI 4.8:1, BCR 2.2:1) following the inclusion of full lifecycle customer costs, scope changes, and updated additional-tax-revenue (ATR) estimates.

The investigation's §6.5 sensitivity check scores the 3.8:1 ROI for directional shift against two inputs: the customer-cost reprice from §6.1 (which inflates the customer-cost side of the appraisal) and the OBR EFO March 2026 ATR forecast (which may have moved since the June 2025 AOA).

Current sensitivity result: {comparison_value}. Drift: {drift_absolute:+.2f} ({drift_percent:+.2f}%).

This is an estimate of the direction and approximate magnitude of the shift implied by the inputs, not a reconstruction of HMRC's Green Book NPV calculation. The limitation is disclosed at every stage.

The 1.3:1 BCR in particular drops below the level at which a programme is typically considered "significant positive value for money" under Green Book guidance. Any further shift in the customer-cost side is therefore material to how the Programme would read under HMT's standard categorisation.

## Methodological caveats

**§7.1 services CPI vs all-items CPI.** The customer-cost input to the ROI sensitivity is derived from the §6.1 reprice, which uses services CPI. The all-items CPI equivalent is reported alongside for comparison but not as the primary sensitivity input.

## Supporting drift calculation

- Drift row IDs: {supporting_drift_ids_list}

## Status

Draft. Not runnable until the §6.1 reprice has been computed AND the OBR EFO 2026-03 ATR observation has been loaded.
