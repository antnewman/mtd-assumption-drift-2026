# Investigation brief: MTD assumption drift at the point of £50k mandation

**Working title:** *Taking inflation into account: a reassessment of the Making
Tax Digital business case at the point of £50k mandation*

**Author:** Ant Newman (ORCID 0000-0002-8612-3647)
**Affiliation:** TortoiseAI
**Status:** In progress (April 2026). Runs in parallel with the Crossrail retrospective.
**Licence:** CC BY 4.0 (written content), MIT (code and data)

## Investigation question

At the point of £50k mandation (6 April 2026), ten months after HMRC's June
2025 restatement of the Making Tax Digital business case, do the key
assumptions still hold when scored against current public external data?

## Anchor: Public Accounts Committee recommendation

This investigation operationalises a recommendation formally made to HMRC by
the House of Commons Public Accounts Committee in its 80th report of Session
2022-23, *Progress with Making Tax Digital* (HC 1333, published 24 November
2023).

Conclusion 4 and the associated recommendation:

> HMRC have not been open enough about the substantial costs that Making Tax
> Digital will impose on many taxpayers. Before finalising its proposals to
> extend Making Tax Digital to lower-income taxpayers, HMRC should fully
> reassess the costs for customers to comply with Making Tax Digital for Self
> Assessment, taking into account inflation and any significant design
> changes made when finalising its plans.

The investigation applies this recommendation. It is not a freelance critique.
It asks a question the UK's parliamentary scrutiny body has formally asked
HMRC to answer.

## Methodology stance

The investigation uses:

- Only publicly available primary sources for the HMRC assumption baselines
- Only publicly available external data series for comparison values
- An open-source analysis tool (the PDA Platform) that anyone can inspect
- An append-only data model so that the state of inputs at any point is
  recoverable

Findings are published alongside the methodology, the data, and the code.
Findings that contradict the expected framing are published with equal
prominence.

## The five assumptions under investigation

The five assumptions are held in `data/assumptions.yaml` and loaded into the
`mtd_2026.assumptions` table. They are the operational spine of the
investigation.

Primary assumption (central to the PAC recommendation):

1. **Average transitional cost per £50k-cohort business = £285.**
   Source: HMRC MTD for ITSA TIIN, published 22 February 2024, republished
   2 September 2025.

Supporting assumptions:

2. **Total transitional cost for above-£30k population = £561m.** Same source.
3. **In-scope population at £50k threshold from April 2026 = 780,000.** Same
   source.
4. **Self Assessment tax gap = 18.5% / £5bn.** Same source.

Downstream result:

5. **Overall programme ROI = 3.8:1 (BCR 1.3:1).** Source: MTD Programme
   Accounting Officer Assessment, published 4 June 2025, signed by
   John-Paul Marks.

## External data sources

Held in `data/external_series.yaml`. Summary:

- **ONS CPI services annual rate (D7NN)** and **CPI services index (D7F5)** for
  compliance cost reprice. These are the correct series for a services cost;
  the all-items CPI (D7BT) is not.
- **DBT Business Population Estimates 2025** (published 2 October 2025) for
  the in-scope population cross-check. Note: this series is classified
  "official statistics in development", not accredited. That status must be
  disclosed.
- **HMRC Measuring Tax Gaps 2025** (published June 2025, covering 2023-24) for
  the tax gap assumption. Note: this series runs two years in arrears. The
  2026 edition will not be available until approximately June 2026, after the
  planned publication window.
- **OBR Economic and Fiscal Outlook** (March 2026 edition) for ATR forecast
  risk.
- **Bank of England Bank Rate** for NPV sensitivity where relevant.

## Three methodological caveats that must be disclosed

Every published output includes these:

1. **Services CPI vs headline CPI.** The investigation uses services CPI
   (D7NN) for reprice calculations. Services inflation has run meaningfully
   above headline CPI for the period in question (4.3% versus 3.0% in
   February 2026). The choice materially affects the drift finding. Using
   all-items CPI would understate the drift and would also be methodologically
   wrong because a services cost should be repriced with a services index.

2. **BPE 2025 status.** The Business Population Estimates series was
   reclassified to "official statistics in development" in 2024, a step down
   from "accredited official statistics". The population assumption carries
   more uncertainty than a headline figure would suggest. Any drift finding
   on population must carry this caveat.

3. **Tax gap lag.** Measuring Tax Gaps 2025 reports on the 2023-24 tax year.
   We compare an HMRC assumption stated in September 2025 against a tax gap
   measurement that pre-dates it by approximately 18 months. This is a real
   limitation. The investigation cannot identify whether the tax gap has
   moved since the assumption was stated; only whether the two are
   approximately consistent.

## Narrative arc (for the published report)

**Stage 1: the NAO and PAC identified a specific problem.** In 2023, HMRC's
business case had understated customer compliance costs. The PAC formally
recommended that HMRC reassess those costs, taking inflation into account.

**Stage 2: HMRC accepted the critique and restated.** The February 2024 TIIN
published updated compliance cost figures. The June 2025 AOA incorporated
full lifecycle customer costs, causing BCR to drop from 2.2:1 to 1.3:1.

**Stage 3: the question the PAC asked is now live again.** Ten months have
passed. Services inflation has run above headline CPI throughout. The PAC's
recommendation is due for another application.

**Stage 4: what modern tooling allows.** We can run that reassessment using
public data, in days rather than months, in a fully reproducible way. The
platform lets us do exactly what the PAC asked HMRC to do.

## What this investigation is not

- It is not a critique of HMRC's integrity or good faith. The NAO has already
  reported that HMRC has implemented 11 of its 13 recommendations.
- It is not a political comment on whether MTD for ITSA is a good policy.
  That is for Parliament.
- It is not a claim that the PDA Platform can replace HMRC's Standard Cost
  Model, OBR forecasting, or internal assurance. It is a demonstration that
  public-data reassessment is now fast enough to be continuous rather than
  episodic.

## Publication approach

Primary artefact: a full analytical report on the Tortoise website, with the
Supabase schema, data, and analysis code linked from it.

Derivative formats: a LinkedIn newsletter version, a short-form version, and
a summary post. Channel-specific framing lives in private notes, not in this
brief.

Zenodo release at publication. DOI tracked in CITATION.cff.

Independent tax-policy review is a prerequisite for publication. No finding
is published without a reviewer's sign-off recorded in the `reviews` table.

## Sequencing note

This investigation runs in parallel with the Crossrail retrospective inside
the PDA Investigations programme. The two cases share the `pda_shared`
Supabase tables and the PDA Platform tooling; their case-specific schemas,
methodologies, and reviewers are independent. Progress on either case does
not block the other.