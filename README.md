# MTD Assumption Drift 2026

**Working title:** *Taking inflation into account: a reassessment of the Making Tax Digital business case at the point of £50k mandation.*

**Part of:** [PDA Investigations](https://github.com/antnewman/pda-investigations)
**Tool:** [PDA Platform](https://github.com/antnewman/pda-platform)
**Author:** Ant Newman CEng (MIET, MIEEE), TortoiseAI. ORCID: [0000-0002-8612-3647](https://orcid.org/0000-0002-8612-3647).
**Status:** In progress (April 2026).
**Licence:** [CC BY 4.0](LICENSES/CC-BY-4.0.txt) for written content, [MIT](LICENSES/MIT.txt) for code and data.

---

## The question

At the point of £50k mandation (6 April 2026), ten months after HMRC's June 2025 restatement of the Making Tax Digital business case, do the key assumptions still hold when scored against current public external data?

## The anchor

This investigation operationalises the formal recommendation made to HMRC by the House of Commons Public Accounts Committee in its 80th report of Session 2022-23, *Progress with Making Tax Digital* (HC 1333, 24 November 2023):

> Before finalising its proposals to extend Making Tax Digital to lower-income taxpayers, HMRC should fully reassess the costs for customers to comply with Making Tax Digital for Self Assessment, taking into account inflation and any significant design changes made when finalising its plans.

It is not a freelance critique. It is an application of a question Parliament's scrutiny body has formally asked HMRC to answer.

## Method in one paragraph

Five HMRC assumptions in [`data/assumptions.yaml`](data/assumptions.yaml) (average transitional cost per business, total transitional cost, in-scope population, Self Assessment tax gap, programme ROI) are scored against public external series in [`data/external_series.yaml`](data/external_series.yaml) (ONS services CPI, ONS all-items CPI for disclosure, DBT Business Population Estimates, HMRC Measuring Tax Gaps, OBR Economic and Fiscal Outlook, Bank of England Bank Rate). All sources carry citation keys into [`data/sources.yaml`](data/sources.yaml). Calculations run through the open-source [PDA Platform](https://github.com/antnewman/pda-platform). Results are appended to a Supabase database and published alongside the methodology.

## Repository layout

- [`INVESTIGATION_BRIEF.md`](INVESTIGATION_BRIEF.md): the case-specific framing, decisions, and investigated assumptions.
- [`methodology.md`](methodology.md): the public-facing methodology document.
- [`data/`](data/): structured inputs. Sources, external series, assumptions.
- `analysis/`: analysis scripts and notebooks.
- `findings/`: findings output. Tables, charts, narrative drafts.
- `sources/`: archived copies of primary sources where licensing permits.
- [`AGENT_CONTEXT.md`](AGENT_CONTEXT.md): standing context for AI coding assistants, shared across PDA Investigations.
- [`CLAUDE.md`](CLAUDE.md): Claude Code project instructions.

## Methodological caveats

Every output of this investigation discloses these caveats.

1. **Services CPI (ONS series D7NN) is the correct reprice index, not all-items CPI.** Services inflation ran at 4.3% annual in February 2026 against 3.0% headline. Using all-items CPI would understate the drift and would be methodologically wrong for a services cost.
2. **Business Population Estimates 2025 is classified as "official statistics in development".** It was reclassified from "accredited official statistics" in 2024. The population cross-check must disclose this status.
3. **Tax gap data lag.** Measuring Tax Gaps 2025 covers the 2023-24 tax year. We can check consistency with an HMRC assumption stated in September 2025; we cannot identify whether the tax gap has moved since.

## Reproducibility and review

Every claim is reproducible from public inputs. Assumption values, external observations, and drift calculations are append-only; historical state stays queryable. Findings require independent domain review, recorded in the `reviews` table, before any publication.

## Citing this investigation

See [`CITATION.cff`](CITATION.cff). A Zenodo DOI is issued on publication.

## Licence

Written content is released under [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Code and structured data are released under [MIT](LICENSES/MIT.txt). See [`LICENSE`](LICENSE) for the combined notice.
