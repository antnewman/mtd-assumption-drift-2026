# Methodology

**Investigation:** Making Tax Digital assumption drift at the point of £50k mandation.
**Version:** 0.1 (initial draft, pre-analysis).
**Last reviewed:** 2026-04-21.

This document describes the method used in this investigation. It is written so that an FT policy correspondent, a tax-policy practitioner (ICAEW, CIOT), and a Public Accounts Committee reader can satisfy themselves that the approach is conservative, reproducible, and defensible. It does not present findings. Findings are published separately in [`findings/`](findings/), gated on independent review.

## 1. Scope

This investigation reassesses five assumptions in HMRC's Making Tax Digital for Income Tax Self Assessment (MTD for ITSA) business case, at the point of the £50k mandation threshold introduced on 6 April 2026. The assumptions are listed in [`data/assumptions.yaml`](data/assumptions.yaml) and enumerated in Section 4.

What it reassesses:

- Whether each assumption, as stated by HMRC, remains consistent with current public external data ten months after the June 2025 restatement of the business case.
- Whether the three mandatory methodological caveats set out in Section 7 are respected throughout the scoring.

What it does not do:

- It does not re-run HMRC's Standard Cost Model. Only HMRC has the microdata for that.
- It does not replace OBR forecasts, HMRC programme assurance, or NISTA Gate Reviews.
- It does not make policy recommendations. Whether MTD for ITSA is a good policy is for Parliament.
- It does not claim that drift in an assumption implies fault on HMRC's part. Assumption values were reasonable at the time they were stated.

## 2. Anchor

The investigation applies the formal recommendation made to HMRC by the House of Commons Committee of Public Accounts in its 80th report of Session 2022-23, *Progress with Making Tax Digital* (HC 1333, 24 November 2023). The relevant text, quoted verbatim:

> HMRC have not been open enough about the substantial costs that Making Tax Digital will impose on many taxpayers. Before finalising its proposals to extend Making Tax Digital to lower-income taxpayers, HMRC should fully reassess the costs for customers to comply with Making Tax Digital for Self Assessment, taking into account inflation and any significant design changes made when finalising its plans.

HMG's formal response is recorded in Treasury Minutes (February 2024). Implementation progress is tracked in the HMRC Accounting Officer Assessment of June 2025. This investigation does not freelance a critique; it operationalises a published parliamentary recommendation.

## 3. The question

At the point of £50k mandation (6 April 2026), ten months after HMRC's June 2025 restatement of the MTD business case, do the five key assumptions still hold when scored against current public external data?

## 4. Assumptions under investigation

All five are recorded as rows in `mtd_2026.assumptions` with stable `assumption_key` values, loaded from [`data/assumptions.yaml`](data/assumptions.yaml).

| Key | Assumption | Baseline value | Source |
|---|---|---|---|
| `transitional_cost_50k_cohort` | Average transitional cost per above-£50k cohort business | £285 (2021 prices) | HMRC TIIN, 22 Feb 2024 (republished 2 Sep 2025) |
| `transitional_cost_total_30k_plus` | Total transitional cost for above-£30k population | £561m (2021 prices) | HMRC TIIN, same |
| `population_50k_cohort` | In-scope population at the £50k threshold from April 2026 | 780,000 | HMRC TIIN, same |
| `self_assessment_tax_gap` | Self Assessment tax gap | 18.5% (approximately £5bn) | HMRC TIIN, same |
| `programme_roi` | Overall MTD Programme return on investment | 3.8:1 (BCR 1.3:1) | HMRC AOA, 4 Jun 2025 |

The primary assumption, and the one most directly targeted by the PAC recommendation, is `transitional_cost_50k_cohort`.

## 5. External data series

All external series used are publicly available. Provider URLs are listed in [`data/external_series.yaml`](data/external_series.yaml) and loaded into `pda_shared.external_series`. Individual observations go into `pda_shared.external_observations`, timestamped and immutable.

**For the compliance cost reprice:**
- **ONS D7NN** (CPI annual rate, services). The correct index for repricing a services cost.
- **ONS D7F5** (CPI index, services, 2015 = 100). For level-based reprice between two specific dates.
- **ONS D7BT** (CPI index, all items, 2015 = 100). Included for disclosure only; see caveat 7.1.
- **ONS D7G7** (CPI annual rate, all items). For comparison and disclosure only.

**For the population cross-check:**
- **DBT BPE 2025** (UK Business Population Estimates 2025), classified "official statistics in development". See caveat 7.2.

**For the tax gap consistency check:**
- **HMRC MTG 2025** (Measuring Tax Gaps 2025, covering 2023-24). See caveat 7.3.

**For the ROI sensitivity:**
- **OBR EFO 2026-03** (Economic and Fiscal Outlook, March 2026 edition).
- **BoE Bank Rate** (Bank of England official Bank Rate). Ancillary, for discount-rate sensitivity.

## 6. Method

The method is a series of scoring steps, one per assumption. Each step produces a row in `mtd_2026.drift_calculations` that records the inputs, the formula applied, the result, and the caveat flags. Calculations are idempotent: given the same inputs, re-running them produces the same row.

**6.1 Transitional cost reprice (primary).** The £285 per-business transitional cost is stated in 2021 prices with a baseline date of 22 February 2024, republished 2 September 2025. It is repriced to a current-price equivalent using the ONS services CPI level (D7F5) from the assumption's pricing base year to the month of the £50k mandation. For the April 2026 mandation, the reprice uses the March 2026 index value as an indicative pre-mandation estimate, and is re-run against the April 2026 index when that value publishes (expected mid to late May 2026). The drift is the current-price equivalent minus the £285 baseline.

**6.2 Total transitional cost reprice.** The £561m aggregate is repriced on the same index and compared to the same baseline. A consistency sub-check confirms that the repriced aggregate is approximately equal to the repriced per-business value multiplied by the aggregate population across the £50k and £30k-£50k cohorts.

**6.3 Population cross-check.** The 780,000 in-scope population is compared to the relevant subset of DBT BPE 2025 (sole traders and landlords with qualifying income above £50k). The cross-check is a plausibility indicator, not a proof. The in-development statistics status of BPE 2025 is disclosed with the result.

**6.4 Tax gap consistency check.** The 18.5% Self Assessment tax gap is compared to the most recently published HMRC Measuring Tax Gaps estimate for the Self Assessment population. Because the published series runs approximately two years in arrears, the check is of consistency, not of drift. We cannot identify whether the gap has moved since the assumption was stated. We can only report whether the stated value is approximately consistent with the latest measurement.

**6.5 ROI sensitivity.** The 3.8:1 ROI and 1.3:1 BCR are scored for sensitivity to two inputs: the customer-cost reprice from 6.1, and the OBR ATR (additional tax revenue) forecast from the March 2026 EFO. We do not reconstruct HMRC's Green Book NPV calculation. We estimate the direction and approximate magnitude of the shift implied by the reprice and the ATR update, and disclose the limitation.

## 7. Mandatory methodological caveats

Every published output discloses these three caveats in full.

**7.1 Services CPI vs all-items CPI.** The investigation uses services CPI (D7NN, D7F5) for the reprice calculations. Services inflation has run meaningfully above headline CPI over the period in question, at 4.3% annual in February 2026 against a 3.0% headline rate. The choice materially affects the drift result. Using all-items CPI would understate the drift and would also be methodologically wrong: compliance time and software are services, not a goods-weighted basket. D7BT and D7G7 are loaded into the database for transparency and may be reported alongside the primary result, but the primary result uses D7NN and D7F5.

**7.2 Business Population Estimates status.** The DBT BPE series was reclassified in 2024 from "accredited official statistics" to "official statistics in development", because of data quality concerns in the Labour Force Survey used to estimate the unregistered portion of the population. The population cross-check in 6.3 discloses this status whenever the BPE figure is cited.

**7.3 Tax gap lag.** HMRC Measuring Tax Gaps 2025 reports the 2023-24 tax year. The MTD TIIN assumption of 18.5% was stated in September 2025 (republication of the February 2024 figure). There is approximately an eighteen-month gap between the tax gap measurement and the assumption statement, and a further gap between the assumption statement and the investigation. The check in 6.4 is of consistency, not of drift. The 2026 edition of Measuring Tax Gaps (covering 2024-25) publishes approximately June 2026, after the intended publication window of this investigation. A follow-up check will be run when it is published.

## 8. Data model and reproducibility

Data is stored in Supabase project `pda-investigations` (ID `bulheatuxvktopxrwbvs`, eu-west-2 London region, free tier).

- `pda_shared.source_documents`: primary source metadata, keyed by `citation_key`.
- `pda_shared.external_series`: external data series metadata.
- `pda_shared.external_observations`: append-only time-series observations.
- `mtd_2026.assumptions`: the five HMRC assumptions, with `is_superseded` flag.
- `mtd_2026.drift_calculations`: the scored outputs, one row per assumption per calculation run.
- `mtd_2026.findings`: narrative findings, public only when `published = true` and an approved review exists in `pda_shared.reviews`.

All tables are append-only. Revisions to a value produce a new row with a new `baseline_date`; the previous row is marked `is_superseded = true`. Historical state is queryable by filtering on date. Row-level security allows public read on most tables; writes require the service role key, which is never committed to git.

Every claim is reproducible from publicly available inputs. If an input is not public, it cannot be used in a published finding.

## 9. Tooling

Analysis runs through the [PDA Platform](https://github.com/antnewman/pda-platform), an open-source Model Context Protocol platform for project and programme data. Code specific to this investigation lives in [`analysis/`](analysis/). Migrations and seed SQL live alongside the PDA Platform's Supabase migration directory, cross-referenced from this repository.

Analysis is deterministic given the inputs. Each run stamps the inputs, the platform version, and a checksum into the result row, so that any reader can reproduce the scored output from the same inputs.

## 10. Independent review

No finding is published without an independent domain reviewer's sign-off recorded in `pda_shared.reviews`. Reviewer consent to be named is explicit per review. The target reviewer profile is an independent domain expert in UK tax administration, typically a Chartered Tax Adviser, an ICAEW member with tax policy specialism, or an academic with published work on small-business tax compliance. A programme-assurance reviewer (for example, someone with NAO or IPA experience) may be added for the methodological framing where appropriate. The review is not pro forma: a sceptical or negative review is published alongside the finding, not hidden from it.

## 11. Publication and update policy

The primary artefact is a full analytical report on the Tortoise website, with the Supabase schema, data, and analysis code linked from it. A Zenodo release with DOI is made at publication. Derivative formats (short-form, LinkedIn, summary) carry the same methodological caveats.

Findings that are boring are published. Findings that contradict expected framing are published with equal prominence to those that do not. The framing can emphasise what is interesting; it cannot hide what is inconvenient.

If HMRC publishes a new TIIN or AOA before publication, the analysis is re-run against the new baseline and the report is revised before release. If a new edition of an external series publishes after release, a follow-up note is appended; the original report is not silently modified.

## 12. Contacts

Author: Ant Newman, TortoiseAI. ORCID [0000-0002-8612-3647](https://orcid.org/0000-0002-8612-3647).

Correspondence on the methodology is welcome as issues on this repository, or to the author's published contact channels.
