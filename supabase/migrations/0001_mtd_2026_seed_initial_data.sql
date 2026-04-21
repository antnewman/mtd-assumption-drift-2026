-- 0001_mtd_2026_seed_initial_data
--
-- Seeds the initial data for the MTD 2026 investigation into an already-
-- migrated schema. Three blocks, in dependency order:
--
--   1. pda_shared.source_documents   (7 rows, from data/sources.yaml)
--   2. pda_shared.external_series    (8 rows, from data/external_series.yaml)
--   3. mtd_2026.assumptions          (5 rows, from data/assumptions.yaml,
--                                    joined against source_documents by
--                                    citation_key).
--
-- Idempotent. Re-running this migration is a no-op where the same
-- citation_key, series_code, or assumption_key already exists.
--
-- The schema is assumed to exist (migration 0001_initial_schema in the
-- Supabase project bulheatuxvktopxrwbvs). This file loads only data; no
-- DDL. Run via `apply_migration` against project bulheatuxvktopxrwbvs.

-- =============================================================
-- 1. Source documents
-- =============================================================

INSERT INTO pda_shared.source_documents
  (citation_key, title, author, publisher, publication_date, last_updated,
   url, document_type, notes)
VALUES
  (
    'HMRC-TIIN-MTD-ITSA-2024-02',
    'Making Tax Digital for Income Tax Self Assessment for sole traders and landlords',
    'HM Revenue and Customs',
    'UK Government',
    DATE '2024-02-22',
    DATE '2025-09-02',
    'https://www.gov.uk/government/publications/extension-of-making-tax-digital-for-income-tax-self-assessment-to-sole-traders-and-landlords/making-tax-digital-for-income-tax-self-assessment-for-sole-traders-and-landlords',
    'TIIN',
    'Primary source for per-business transitional cost, total transitional cost, in-scope population, and SA tax gap assumptions. Originally published February 2024, republished September 2025 with scope changes announced at Spring Statement 2025 noted in the preamble. The core SCM-derived cost figures are unchanged between the two versions.'
  ),
  (
    'HMRC-AOA-MTD-2025-06',
    'Making Tax Digital Programme Accounting Officer''s Assessment summary (updated)',
    'HM Revenue and Customs',
    'UK Government',
    DATE '2025-06-04',
    NULL,
    'https://www.gov.uk/government/publications/making-tax-digital-programme-accounting-officer-assessment-updated/making-tax-digital-programme-accounting-officers-assessment-summary-updated',
    'AOA',
    'Signed by John-Paul Marks, Chief Executive HMRC, on 4 June 2025. Supersedes the April 2024 AOA. Source for the overall programme BCR 1.3:1 and ROI 3.8:1. Notes that the BCR dropped from 2.2:1 and the ROI from 4.8:1 as a direct consequence of including full lifecycle customer costs, scope changes, and updated ATR estimates.'
  ),
  (
    'HMRC-TIIN-MTD-ITSA-2028-20k',
    'Reduction of the mandation threshold from £30,000 to £20,000 from April 2028',
    'HM Revenue and Customs',
    'UK Government',
    DATE '2025-03-26',
    NULL,
    'https://www.gov.uk/government/publications/making-tax-digital-for-income-tax-self-assessment-reducing-the-mandation-threshold-from-30000-to-20000-from-april-2028/reduction-of-the-mandation-threshold-from-30000-to-20000-from-april-2028',
    'TIIN',
    'TIIN covering the £20k threshold cohort announced at Spring Statement 2025. Cites approximately 970,000 additional individuals brought into scope for April 2028. Referenced here for completeness; the primary investigation focuses on the £50k cohort mandated April 2026.'
  ),
  (
    'NAO-MTD-2023',
    'Progress with Making Tax Digital',
    'Comptroller and Auditor General, National Audit Office',
    'UK National Audit Office',
    DATE '2023-06-12',
    NULL,
    'https://www.nao.org.uk/reports/progress-with-making-tax-digital/',
    'NAO_REPORT',
    'HC 1319, Session 2022-23. The NAO''s investigation of progress with MTD. Found that HMRC had understated customer costs in successive business cases: excluded £1.5bn upfront transitional costs in May 2022 business case, and excluded upfront customer costs entirely in March 2023 business case. Made 13 recommendations. Per the June 2025 AOA, 11 have been implemented and 2 are on track for 2025.'
  ),
  (
    'PAC-MTD-2023',
    'Progress with Making Tax Digital',
    'House of Commons Committee of Public Accounts',
    'UK Parliament',
    DATE '2023-11-24',
    NULL,
    'https://publications.parliament.uk/pa/cm5803/cmselect/cmpubacc/1333/report.html',
    'PAC_REPORT',
    'HC 1333, 80th report of Session 2022-23. The PAC report that followed the NAO investigation and oral evidence from Jim Harra, Permanent Secretary and Chief Executive HMRC. Conclusion 4 is the anchor for this investigation: "HMRC have not been open enough about the substantial costs that Making Tax Digital will impose on many taxpayers." Associated recommendation: HMRC should "fully reassess the costs for customers to comply with Making Tax Digital for Self Assessment, taking into account inflation and any significant design changes".'
  ),
  (
    'HMT-TreasuryMinutes-MTD-2024-02',
    'Treasury Minutes: Government response to PAC 80th report (Progress with Making Tax Digital)',
    'HM Treasury',
    'UK Government',
    DATE '2024-02-08',
    NULL,
    'https://www.gov.uk/government/publications/treasury-minutes-february-2024',
    'TREASURY_MINUTES',
    'HMG''s formal response to each of the PAC''s five substantive recommendations. Of five, HMG agreed with two, disagreed with three. Used as corroborating evidence that the PAC critique is on the record and was formally engaged with by HMRC.'
  ),
  (
    'HMRC-MTG-2025',
    'Measuring tax gaps 2025 edition: tax gap estimates for 2023 to 2024',
    'HM Revenue and Customs',
    'UK Government',
    DATE '2025-06-19',
    NULL,
    'https://www.gov.uk/government/statistics/measuring-tax-gaps',
    'OFFICIAL_STATISTICS',
    'The 2025 edition of HMRC''s annual tax gap publication, covering the 2023-24 tax year. Reports total UK tax gap at 5.3% / £46.8bn and VAT gap at 5.0%. Used to cross-check the Self Assessment tax gap assumption (18.5%) cited in the MTD TIIN. Note: the 2026 edition covering 2024-25 will publish approximately June 2026.'
  )
ON CONFLICT (citation_key) DO NOTHING;

-- =============================================================
-- 2. External series
-- =============================================================

INSERT INTO pda_shared.external_series
  (series_code, series_name, provider, unit, frequency, lag_days,
   status, source_url, notes)
VALUES
  (
    'ONS-D7NN',
    'CPI annual rate: Services, 2015=100',
    'ONS',
    'percent',
    'monthly',
    30,
    'accredited',
    'https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7nn/mm23',
    'Primary series for repricing the services-component compliance cost assumption. Services inflation has diverged meaningfully from headline CPI over 2024-25 and into 2026. Using all-items CPI (D7BT) instead would be methodologically wrong for a services cost. February 2026 value: 4.3% annual.'
  ),
  (
    'ONS-D7F5',
    'CPI index: Services, 2015=100',
    'ONS',
    'index_2015_100',
    'monthly',
    30,
    'accredited',
    'https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7f5/mm23',
    'Services CPI index level, for level-based reprice rather than rate-based. Useful when comparing price levels at two different baseline dates (e.g. September 2025 TIIN vs April 2026 point of mandation).'
  ),
  (
    'ONS-D7BT',
    'CPI index: All items, 2015=100',
    'ONS',
    'index_2015_100',
    'monthly',
    30,
    'accredited',
    'https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23',
    'Headline all-items CPI index. Included for comparison and disclosure only. The research brief originally cited this series as the reprice measure; this was incorrect. We use D7NN for services costs and note the divergence between the two explicitly in the methodology.'
  ),
  (
    'ONS-D7G7',
    'CPI annual rate: All items, 2015=100',
    'ONS',
    'percent',
    'monthly',
    30,
    'accredited',
    'https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7g7/mm23',
    'Headline all-items CPI annual rate. For comparison with D7NN. February 2026 value: 3.0% annual.'
  ),
  (
    'DBT-BPE-2025',
    'UK Business Population Estimates 2025',
    'DBT',
    'count',
    'annual',
    275,
    'in_development',
    'https://www.gov.uk/government/statistics/business-population-estimates-2025',
    'Department for Business and Trade estimate of the UK private-sector business population. At the start of 2025: 5.7 million businesses, of which 4.3 million had no employees. Reclassified to "official statistics in development" in 2024, a step down from "accredited official statistics". The reclassification is tied to the Labour Force Survey data used to estimate the unregistered portion of the population. This status must be disclosed when the in-scope population assumption is discussed.'
  ),
  (
    'HMRC-MTG-2025',
    'Measuring Tax Gaps: Self Assessment tax gap',
    'HMRC',
    'percent',
    'annual',
    730,
    'accredited',
    'https://www.gov.uk/government/statistics/measuring-tax-gaps',
    'HMRC''s estimate of the tax gap attributable to Self Assessment businesses. The 2025 edition (published June 2025) reports the 2023-24 tax year. The two-year lag means we cannot identify whether the SA tax gap has moved since the September 2025 TIIN was published; only whether the TIIN''s 18.5% figure is consistent with the most recently published measurement. The 2026 edition (2024-25 data) is expected approximately June 2026, after our publication window.'
  ),
  (
    'OBR-EFO-2026-03',
    'OBR Economic and Fiscal Outlook, March 2026',
    'OBR',
    'narrative_plus_scorecard',
    'biannual',
    0,
    'accredited',
    'https://obr.uk/efo/',
    'The Office for Budget Responsibility''s biannual macroeconomic and fiscal forecast. The March 2026 edition is the most recent at the time of this investigation. Contains OBR''s certification of MTD additional tax revenue forecasts and the underlying tax-gap trajectory assumed at fiscal events. Used for cross-checking the ATR and ROI downstream assumptions.'
  ),
  (
    'BOE-BASERATE',
    'Bank of England official Bank Rate',
    'Bank of England',
    'percent',
    'event_driven',
    0,
    'accredited',
    'https://www.bankofengland.co.uk/monetary-policy/the-interest-rate-bank-rate',
    'The Bank Rate as set by the Monetary Policy Committee. Used for discount rate sensitivity analysis where the business case applies a Green Book 3.5% real discount rate. Ancillary rather than primary to the investigation.'
  )
ON CONFLICT (series_code) DO NOTHING;

-- =============================================================
-- 3. Assumptions
--
-- Joined against pda_shared.source_documents by citation_key to resolve
-- source_document_id. Guarded by NOT EXISTS on assumption_key so a
-- second run is a no-op.
-- =============================================================

INSERT INTO mtd_2026.assumptions
  (assumption_key, assumption_label, assumption_description, value, unit,
   baseline_date, pricing_base_year, source_document_id, source_location,
   is_primary, is_superseded, pac_recommendation_ref, notes)
SELECT
  v.assumption_key,
  v.assumption_label,
  v.assumption_description,
  v.value,
  v.unit,
  v.baseline_date,
  v.pricing_base_year,
  sd.id,
  v.source_location,
  v.is_primary,
  false AS is_superseded,
  v.pac_recommendation_ref,
  v.notes
FROM (
  VALUES
    (
      'transitional_cost_50k_cohort',
      'Average transitional cost per £50k-cohort business',
      'HMRC''s estimate of the average one-off compliance cost incurred by a business in the above-£50k Self Assessment cohort as a consequence of meeting MTD for ITSA obligations from April 2026. Derived using HMRC''s Standard Cost Model methodology. Includes time spent on familiarisation, in-house training, hardware upgrades where applicable, and additional accountancy costs. Excludes continuing costs (which are captured in a separate annual compliance cost figure).',
      285.00::numeric,
      'gbp_per_business',
      DATE '2024-02-22',
      2021,
      'HMRC-TIIN-MTD-ITSA-2024-02',
      'Section ''Impact on business including civil society organisations'': ''Estimated one-off impact on administrative burden'' table, ''Above £50,000 threshold'' column',
      true,
      'PAC-MTD-2023 Conclusion 4 and associated recommendation',
      'This is the primary assumption under investigation. The PAC specifically asked HMRC to reassess this figure taking inflation into account. The underlying Standard Cost Model research pre-dates the baseline date of the TIIN; the 2024-02 TIIN is the first publication of this figure as the authoritative HMRC position.'
    ),
    (
      'transitional_cost_total_30k_plus',
      'Total transitional cost for above-£30k population',
      'The aggregate one-off compliance cost estimate for the total mandated population above the £30k threshold (covering both the April 2026 £50k cohort and the April 2027 £30k-£50k cohort). Equals the per-cohort averages multiplied by the respective populations.',
      561000000.00::numeric,
      'gbp',
      DATE '2024-02-22',
      2021,
      'HMRC-TIIN-MTD-ITSA-2024-02',
      '''Estimated one-off impact on administrative burden'' table, ''Total mandated population above £30,000'' column, ''Costs'' row',
      false,
      'PAC-MTD-2023 Conclusion 4',
      'A cross-check on the primary assumption: value should approximately equal transitional_cost_50k_cohort * population_50k_cohort, plus the equivalent for the £30k-£50k cohort. Breakdown per TIIN: £223m for the above-£50k threshold and £338m for the £30k-£50k threshold.'
    ),
    (
      'population_50k_cohort',
      'In-scope population at £50k threshold from April 2026',
      'HMRC''s estimate of the number of sole traders and landlords with qualifying income above £50,000 who will be mandated into MTD for ITSA from 6 April 2026. Derived from HMRC Self Assessment return data.',
      780000::numeric,
      'count',
      DATE '2024-02-22',
      NULL::integer,
      'HMRC-TIIN-MTD-ITSA-2024-02',
      'Section ''Impact on business including civil society organisations'': ''Who is affected'' paragraph',
      false,
      NULL,
      'A further 970,000 people in the £30k-£50k band are expected to join from April 2027 (same source). The April 2028 £20k cohort is estimated at approximately 970,000 additional individuals per the separate March 2025 TIIN (HMRC-TIIN-MTD-ITSA-2028-20k).'
    ),
    (
      'self_assessment_tax_gap',
      'Self Assessment tax gap',
      'HMRC''s estimate of the tax gap for Self Assessment businesses, cited in the TIIN''s policy objective section as motivation for MTD for ITSA. Expressed as both a percentage of theoretical SA liability and an absolute figure.',
      18.50::numeric,
      'percent',
      DATE '2024-02-22',
      NULL::integer,
      'HMRC-TIIN-MTD-ITSA-2024-02',
      'Section ''Policy objective'', paragraph 2',
      false,
      NULL,
      'Value also stated in absolute terms as approximately £5bn. This assumption supports the additional tax revenue side of the business case. Cross-check against HMRC-MTG-2025 is a consistency check, not a drift calculation, because of the two-year lag in tax gap estimates.'
    ),
    (
      'programme_roi',
      'Overall MTD Programme return on investment',
      'The headline return on investment ratio for the MTD Programme as a whole, comparing exchequer benefits to HMRC (government) programme costs, excluding customer costs in line with Green Book guidance. The associated overall benefit-cost ratio (BCR), which does include customer costs, is 1.3:1.',
      3.80::numeric,
      'ratio',
      DATE '2025-06-04',
      NULL::integer,
      'HMRC-AOA-MTD-2025-06',
      'Section 3 (Value for money), paragraph discussing ''overall BCR'' and ''ROI'', directly after reference to CIDC and HMT approval',
      false,
      NULL,
      'The BCR dropped from 2.2:1 to 1.3:1 and the ROI from 4.8:1 to 3.8:1 between the April 2024 AOA and the June 2025 AOA. HMRC attributes this to the inclusion of full lifecycle customer costs, scope changes, and updated ATR and customer cost estimates. The drop is itself evidence that HMRC has operationalised the PAC''s recommendation to be more open about customer costs.'
    )
) AS v(
  assumption_key, assumption_label, assumption_description, value, unit,
  baseline_date, pricing_base_year, citation_key, source_location,
  is_primary, pac_recommendation_ref, notes
)
JOIN pda_shared.source_documents sd
  ON sd.citation_key = v.citation_key
WHERE NOT EXISTS (
  SELECT 1 FROM mtd_2026.assumptions a WHERE a.assumption_key = v.assumption_key
);
