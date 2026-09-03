# WORLD SIGNALS — Energy / Commodities Correction K transaction audit v0.1

**Reference date:** 2026-09-03  
**Coverage programme:** `WSCP-ENERGY-COMMODITIES-CORRECTION-K`  
**Migration commit:** `b142b377b9bd5280a275a7e5b9c67fe6b86777a6`

## Purpose

Correction K is a deliberately small non-monetary coverage repair selected after the v0.18 global coverage, physical-risk, health/biosecurity, energy/commodities and South Asia audits.

It does not attempt broad category balancing. It adds only the candidates that simultaneously cleared marginal-value, timing-precision, ontology and provenance gates.

## Canonical transaction

Before:

- canonical registry v0.18;
- 662 occurrences;
- source registry v1.49.

After:

- canonical registry **v0.19**;
- **668 occurrences**;
- source registry **v1.50**;
- +6 occurrences;
- +3 series;
- +3 source institutions.

No monitor expectations or monitor operations policy changed. Automatic canonical commit remained false. Google Calendar writes remained false.

## Added series

### JODI Oil + Gas World Database updates

One `SOURCE_BUNDLE` occurrence per official first monthly update, containing two data products:

- JODI-Oil World Database update;
- JODI-Gas World Database update.

Remaining 2026 occurrences:

- `WSO-COM-A-0053` — 22 Sep 2026, 12:00 Europe/London / 11:00Z;
- `WSO-COM-A-0054` — 21 Oct 2026, 12:00 Europe/London / 11:00Z;
- `WSO-COM-A-0055` — 19 Nov 2026, 12:00 Europe/London / 12:00Z;
- `WSO-COM-A-0056` — 21 Dec 2026, 12:00 Europe/London / 12:00Z.

Source: `WSSRC-COM-012`.

### GECF Summit of Heads of State and Government

- `WSO-COM-A-0057` — 27 Oct 2026, Moscow, date-only precision.
- Source: `WSSRC-COM-013`.

### International Copper Study Group meetings

- `WSO-COM-A-0058` — 13 Oct 2026, Lisbon, date-only precision.
- Source: `WSSRC-COM-014`.

## Source governance

All three source records are explicitly **production automation holds**.

- JODI: rights-reserved factual-metadata/manual-provenance classification;
- GECF: rights audit required before automated retrieval;
- ICSG: rights audit required before automated retrieval.

Canonical factual provenance was therefore admitted without implying crawler or redistribution permission.

## Identity-reconciliation incident

The first read-only preflight failed closed because the initial planned commodity IDs were already occupied.

Diagnostic run `33765743527` established:

- `WSO-COM-A-0029` through `0039`: USDA/ABARES agricultural-commodity records;
- `WSO-COM-A-0040` through `0048`: FAO/AMIS records;
- `WSO-COM-A-0049` through `0052`: physical-risk windows;
- `WSSRC-COM-010`: FAO;
- `WSSRC-COM-011`: AMIS/FAO;
- no existing JODI, GECF or ICSG institution/series identity.

The existing identities were preserved. Correction K was reconciled to the next free occurrence block `0053–0058` and source block `012–014`. The transaction script was then made plan-driven so future identity reconciliation does not require duplicated hard-coded sequences.

This incident is evidence that the stable-identity preflight is functioning as intended.

## Transaction safety evidence

The successful one-shot write run required all of the following to pass:

- fresh in-memory fail-closed preflight;
- JODI Europe/London → UTC round-trip validation;
- JODI `SOURCE_BUNDLE` two-product assertion;
- canonical registry validation;
- coverage regression tests;
- exact v0.19 / 668 and source v1.50 postconditions;
- all new sources remain `PRODUCTION_AUTOMATION_HOLD`;
- monitor expectations and monitor policy SHA-256 unchanged before/after;
- changed-file set exactly `data/canonical/registry.json` and `data/sources/registry.json`.

The temporary write-capable workflow was removed immediately after successful migration. The read-only preflight workflow was subsequently removed as completed machinery. Plan and transaction script remain as inert reproducibility evidence.

## Re-audit requirement

Do not infer success merely from six new rows. The v0.19 coverage audit must measure whether the correction actually improves series/institution diversity and reduces oil-specific concentration without materially worsening overall schedule-rich-category dominance.

Expected mechanical direction, to be verified by the read-only audit:

- ENERGY_COMMODITIES occurrences: 28 → 34;
- unique series: 6 → 9;
- unique institutions: 3 → 6;
- explicitly oil-specific legacy occurrences remain 23, while new JODI is a combined oil+gas bundle rather than an oil-only series.

The measured post-audit result should determine the next action; no further energy population follows automatically from this transaction.
