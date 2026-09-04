# WORLD SIGNALS — provenance-scope repair A research v0.1

**Reference date:** 2026-09-04  
**Repository checkpoint:** `7bf983d59859e60de24dad086f42bc5526726333`  
**Canonical registry:** v0.20 / 669  
**Source registry:** v1.60 / 223  
**Monitor expectations:** v0.7  
**Scope:** resolve the two standing provenance-scope holds, Brazil TSE `WSSRC-EL-BR-001` and Swiss National Bank `WSSRC-CB-009`, without changing any event date or stable occurrence identity.

## Why this is a separate repair

These two records were deliberately excluded from P1-A through P1-H because their problem was not merely missing governance metadata.

- Brazil: one canonical inauguration occurrence points to an electoral-calendar source that does not establish the constitutional term-start rule.
- Switzerland: the registered SNB decisions/history page describes monetary-policy decisions but is not the forward event-schedule surface from which the existing 2026–2028 assessment, news-conference and summary dates were populated.

Ordinary governance backfill would have legitimised the wrong provenance relationship. The repair must correct source scope first, preserve occurrence identities and dates, then classify the repaired source records.

## Read-only repository diagnostic

Temporary read-only run `33882678520` inventoried both source records and every canonical dependency at merged source v1.60 / canonical v0.20.

### Brazil TSE

`WSSRC-EL-BR-001` currently has four canonical dependencies:

1. `WSO-EL-A-0001` — first round, 4 October 2026;
2. `WSO-EL-A-0002` — conditional second round, 25 October 2026;
3. `WSO-EL-A-0003` — diplomation deadline;
4. `WSO-EL-A-0004` — presidential inauguration, 5 January 2027.

The first three belong to the TSE electoral-calendar source family. The fourth does not.

### Swiss National Bank

`WSSRC-CB-009` has 18 canonical dependencies: six monetary-policy assessment press releases, six associated news conferences and six summaries of monetary-policy discussion from September 2026 through January 2028. All 18 exact dates/times are present on the SNB forward event schedule.

No existing change-ledger entry references either held source or `WSO-EL-A-0004`.

## Brazil — authoritative source decomposition

### TSE electoral calendar

Authoritative resolution:

https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-760-de-2-de-marco-de-2026

Amending resolution:

https://www.tse.jus.br/legislacao/compilada/res/2026/resolucao-no-23-771-de-3-de-agosto-de-2026

The consolidated TSE calendar establishes the 2026 election timetable, including the 4 October first round, the conditional 25 October second round and the election-administration/diplomation timetable. `WSSRC-EL-BR-001` therefore remains a valid stable source identity for those three canonical dependencies.

Brazilian Copyright Law 9.610/1998, art. 8, excludes laws, regulations, judicial decisions and other official acts from copyright protection and separately excludes common-use information such as calendars and agendas. This supports curated factual use of the electoral-resolution schedule. It does **not** by itself authorise arbitrary automated retrieval of the TSE website.

Frozen post-repair classification for `WSSRC-EL-BR-001`:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

Its canonical dependency count becomes **3**, not 4.

### Constitution art. 82

Official constitutional text:

https://www4.planalto.gov.br/legislacao/portal-legis/legislacao-1/constituicao

Constitutional Amendment 111/2021:

https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/emc111.htm

Article 82 states that the four-year presidential mandate begins on **5 January of the year following the election**. The date of `WSO-EL-A-0004` is therefore correct; its source relationship is not.

A new source identity is required rather than broadening the TSE source into a cross-institution composite:

- `WSSRC-EL-BR-002` — Presidency of the Republic / official Constitution art. 82 term-commencement rule.

The Presidency's Portaria 130/2021 states that content of the Portal da Legislação is freely accessible and may be used, reproduced and shared with or without profit, subject to source attribution for derivative works and the portal's informational-status caveat. Copyright Law art. 8 independently excludes official legal acts from copyright protection.

Frozen classification for `WSSRC-EL-BR-002`:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

The new source has exactly **1** canonical dependency after repair.

## Brazil canonical repair — one occurrence only

`WSO-EL-A-0004` remains the same stable occurrence with the same series, date, lifecycle, condition and election-process links.

Only provenance-semantic fields are authorised to change:

- `source_id`: `WSSRC-EL-BR-001` → `WSSRC-EL-BR-002`;
- `institution`: `Tribunal Superior Eleitoral` → `Presidency of the Republic of Brazil`;
- `election_date_basis`: `EXPLICIT_ELECTORAL_AUTHORITY_SCHEDULE` → `CONSTITUTIONAL_RULE_DERIVED`;
- `primary_source_assertion_id` and `last_successful_assertion_id`: recomputed because source identity is part of deterministic assertion identity;
- `last_verified_at`: refreshed to the repair review date.

The exact deterministic post-repair assertion ID is `WSA-66b042250a27801e`.

The following must remain unchanged:

- occurrence ID `WSO-EL-A-0004`;
- series ID `WSER-EL-BR-GEN`;
- `start_local = 2027-01-05`;
- all-day/day precision;
- conditional-on-result semantics;
- result dependency on `WSO-EL-A-0001`;
- lifecycle/certainty status;
- market/geopolitical importance fields;
- stable election-process identity.

Canonical version may advance **v0.20 → v0.21** for the reviewed provenance correction, but canonical count remains **669**.

The change ledger must record the old/new source identity, institution, election-date basis and assertion identity. This is a provenance correction, not a reschedule and not evidence for reopening the automatic canonical-commit gate.

## Swiss National Bank — endpoint repair

Current registered URL:

https://www.snb.ch/en/the-snb/mandates-goals/monetary-policy/decisions

Correct forward schedule:

https://www.snb.ch/en/services-events/digital-services/event-schedule

Copyright / use terms:

https://www.snb.ch/en/srv/disclaimer_copyright

The decisions page correctly explains the SNB's monetary-policy publication model, but the dedicated event schedule is the authoritative forward timing surface. On current official evidence it lists every existing `WSSRC-CB-009` canonical dependency through 13 January 2028 at the exact times already stored in WORLD SIGNALS.

Therefore:

- keep stable source ID `WSSRC-CB-009`;
- replace its authoritative URL with the event schedule;
- make the endpoint role/information supplied explicitly cover forward assessments, news conferences and summaries;
- retain the decisions page as a supporting/backup source rather than the primary forward schedule;
- preserve all 18 canonical occurrences byte-for-byte;
- retain the existing non-commercial reuse conditions;
- do not infer automated-access permission from those reuse terms.

Frozen post-repair classification:

- `canonical_provenance_use = CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use = ENDPOINT_REVIEW_REQUIRED`
- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`

The 18-source dependency count remains unchanged.

## Transaction boundary

A later guarded transaction, and only that transaction, may alter:

1. `data/canonical/registry.json` — one occurrence's provenance-semantic fields; count unchanged;
2. `data/sources/registry.json` — repaired TSE row, repaired SNB row, one new constitutional source, registry version/count metadata;
3. `data/changes/ledger.json` — one reviewed provenance-repair entry and ledger version/reference metadata.

It must leave monitor expectations and live-monitor code byte-identical, keep automatic canonical commit false, keep Google Calendar writes false, preserve all 669 occurrence IDs, and preserve every canonical date/time.

The source registry post-state is **v1.61 / 224**. No P1-I tranche is authorised by this repair.