# WORLD SIGNALS — Post-AN pressure audit AO v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `35bcb5616e99c7fce58f82cfc14bfed901929f3a`  
**Architecture position:** Analysis selection/methodology audit  
**Mutation policy:** read-only selection audit; no canonical, source, ledger, overlay, monitor, Calendar, Analysis-review or Analysis-evidence mutation

## Verified post-AN checkpoint

- Canonical registry: **v0.37 / 687**
- Source registry: **v1.78 / 242**
- Change ledger: **v0.24 / 59**
- Biosecurity overlay: **v0.12 @ canonical v0.37 / 687**
- Monitor expectations: **v0.9**
- Analysis schema: **v0.4**
- Analysis reviews: **v0.12 / 16**
- Analysis evidence: **v0.12 / 67**
- completed Analysis-eligible occurrences: **20**
- reviewed occurrences: **16**
- reviewed event-type diversity: **14**
- production `EXACT_TIMESTAMP_SERIES` rows: **0**
- completed-but-unreviewed frontier: **4**

## Remaining choice set

| Occurrence | Category / event type | Marginal value after AN |
| --- | --- | --- |
| `WSO-CLIM-UNFCCC-SB64-202606` | CLIMATE_ENVIRONMENT / ENVIRONMENTAL_GOVERNANCE_EVENT | first reviewed climate-governance type; global institution; tests closure vs substantive resolution and subsidiary-body output vs later COP/CMA adoption; strengthened by first-party post-session reports published 28 Aug 2026 |
| `WSO-HEALTH-WHA-079` | HEALTH_BIOSECURITY / HEALTH_GOVERNANCE_EVENT | first reviewed health-governance type with many formal resolutions/decisions; strong but overlaps the institutional-process contract already exercised by W and would deepen existing WHO concentration |
| `WSO-TRD-EU-RU-SANC-20260625` | TRADE_SANCTIONS_INDUSTRIAL_POLICY / SANCTIONS_PROCESS | novel legal-policy type and clean first-party act; another European specimen and comparatively simpler analytical boundary |
| `WSO-MAC-B-0041` | MACROECONOMIC_RELEASE / DATA_RELEASE | current Japanese household-spending release; institution novelty but repeats a heavily exercised macro/data-release contract |

The set remains a **choice set, not a backlog**.

## Upstream consistency check

Fresh official research rechecked the EU sanctions anchor before selection. The Council of the EU's 25 June 2026 notice states that the economic restrictive measures were renewed for **12 months, until 31 July 2027**, following the 18–19 June European Council agreement. The existing AE research and forward boundary already encode that twelve-month horizon correctly. No Canonical/Source correction outranks Analysis at this checkpoint.

## New evidence availability changes the SB64 ranking

When AH admitted the SB64 historical anchor, the canonical object correctly captured the 8–18 June Bonn meeting window and first-party closure but did not need to encode detailed negotiating outcomes.

Since then, UNFCCC has published the formal post-session reports on **28 August 2026**:

- `FCCC/SBI/2026/15` and `FCCC/SBI/2026/15/Add.1` for SBI 64;
- `FCCC/SBSTA/2026/5` and `FCCC/SBSTA/2026/5/Add.1` for SBSTA 64.

The addenda explicitly contain **draft decisions forwarded for consideration and adoption** by higher UNFCCC decision bodies. This materially improves the evidence basis for a climate-governance Analysis specimen without changing canonical provenance.

UNFCCC's Q2 2026 institutional update characterises SB64 as delivering **mixed results and progress**: good headway on several issues, inadequate progress on others. The Executive Secretary's closing statement likewise records significant remaining divides while identifying progress in areas including just transition.

These are post-event institutional assessments, not ex-ante forecasts and not a basis for a synthetic scalar success score.

## Schema-pressure check

Analysis schema **v0.4 remains adequate**.

SB64 does not require a new `MIXED` surprise model. The event itself had mixed substantive outcomes, but `what_surprised` measures outcome versus a defensible prior benchmark, not whether the outcome contains both progress and unresolved issues. No reviewed pre-event benchmark establishes how many agenda items, draft decisions or workstreams should have been resolved by 18 June.

Therefore:

- substantive outcome may be described as mixed;
- `what_surprised.status` remains `NOT_ESTABLISHED` unless a defensible contemporaneous benchmark is found;
- no count of agenda items, draft texts or forwarded decisions becomes a scalar progress metric.

## Selection — UNFCCC June Climate Meetings (SB64)

AO selects `WSO-CLIM-UNFCCC-SB64-202606`.

It has the highest marginal value after AN because it tests four boundaries together:

1. **Completion boundary.** The 8–18 June meeting completed; that does not mean negotiations succeeded or every agenda item resolved.
2. **Institutional-identity boundary.** SB64 is an umbrella label over legally distinct `SBI 64` and `SBSTA 64`; Analysis must preserve that distinction rather than fabricate one merged negotiating body.
3. **Decision-chain boundary.** Draft decisions forwarded by subsidiary bodies are observed process outputs. Forwarding is not adoption by COP/CMP/CMA and does not guarantee later adoption unchanged.
4. **Outcome-versus-surprise boundary.** UNFCCC itself characterises results as mixed, but a mixed outcome is not automatically a `MIXED` surprise without a prior comparison basis.

The specimen also adds climate-governance analysis to a sample that already contains physical-climate-risk analysis but no reviewed climate-treaty-governance event.

## Intended Analysis classification

Unless exact-base preflight finds an upstream defect:

- `what_happened`: record formal closure, mixed progress, significant unresolved divides, and separate SBI/SBSTA post-session reports/draft-decision addenda;
- `what_was_expected`: official session scope and mandated workstreams only, not an invented agreement forecast;
- `what_surprised.status = NOT_ESTABLISHED`;
- `what_moved = []`;
- `what_appears_connected`: `LEGAL_OR_OPERATIONAL_DEPENDENCY` / `NOT_A_CAUSAL_CLAIM` / `HIGH`, because subsidiary-body outputs feed later higher-body consideration;
- `second_order_effects.status = OBSERVED` only for the observed creation/forwarding of formal future-decision inputs; later adoption remains unresolved;
- retain alternatives, noise tests and falsifiers.

## Temporal and causal guardrails

- `MULTI_DAY_LOCAL` 8–18 June **does not** acquire synthetic UTC endpoints.
- The 23:45 closure update is completion evidence, **not** the canonical end time.
- SB64 umbrella **does not** merge SBI 64 and SBSTA 64 into one legal session.
- Meeting closure **does not** imply substantive negotiating success.
- 'Mixed results' **does not** itself establish a `MIXED` surprise.
- Draft decisions forwarded **do not** equal adopted COP/CMP/CMA decisions.
- Number of agenda items, draft texts or forwarded decisions **does not** become a scalar progress metric.
- The Executive Secretary's closing statement is institutional interpretation/context, not a consensus decision text.
- Post-session reports published 28 August **do not retime** the June occurrence.
- No market observation is required to make climate governance analytically consequential.
- Production exact-series population remains optional and **0 is valid**.
- Canonical, source, ledger, overlay, monitor and Calendar layers remain protected from AO Analysis writes.
- Remaining completed/unreviewed occurrences remain later choices, not compulsory queue items.
- No auto-merge.

## Decision

**Selected next tranche: UNFCCC SB64 climate-governance Analysis AO**, contingent on exact-base read-only preflight.
