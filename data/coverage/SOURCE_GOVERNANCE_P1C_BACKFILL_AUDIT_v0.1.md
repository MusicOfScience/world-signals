# WORLD SIGNALS — P1-C source-governance backfill audit v0.1

**Reference date:** 2026-09-04  
**Scope:** six reviewed P1-C canonical-dependent source records.  
**Authority:** measured post-transaction audit only; this record does not authorise bulk governance backfill, canonical mutation, monitor expansion or Calendar writes.

## Before

P1-C began from source registry **v1.54 / 223**, canonical **v0.20 / 669**, monitor expectations **v0.7**. The measured post-P1-B state was:

- fully explicit modern governance: **19**;
- sources missing one or more governance fields: **204**;
- P0 configured-monitor backlog: **0**;
- P1 canonical-dependent backlog: **133**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **194**;
- missing `automated_monitoring_use`: **194**;
- missing `verification_mode`: **204**.

## Frozen P1-C cohort

| Source | Institution / surface | Dependencies | Canonical provenance | Automation | Verification |
|---|---|---:|---|---|---|
| `WSSRC-MAC-005` | Eurostat release calendar | 12 | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` |
| `WSSRC-CB-008` | Bank of Canada | 11 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-FIS-007` | Japan MOF JGB auctions | 10 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` |
| `WSSRC-EL-NZ-001` | Electoral Commission New Zealand | 6 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-CN-013` | PBoC financial-statistics rule | 5 | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` |
| `WSSRC-INT-027` | UNGA mandated events | 5 | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `PROHIBITED_OR_RIGHTS_HOLD` | `RIGHTS_HELD_MANUAL_ONLY` |

Eurostat automation clearance is bounded to the expressly provided internet-calendar subscription/feed route; it is not a blanket permission for arbitrary scraping. PBoC source-native precision remains a latest-publication window **within 20 days after month-end**, not an inferred exact date.

## Held-source controls

Two source relationships were excluded unchanged:

- `WSSRC-EL-BR-001` Brazil TSE: the 5 January 2027 presidential inauguration remains constitutionally grounded rather than properly evidenced by the electoral-calendar source relationship;
- `WSSRC-CB-009` Swiss National Bank: the registered decisions/history URL does not directly support the forward monetary-policy assessment schedule, which resides on a separate SNB event-schedule surface.

The Brazil inauguration guard remained exactly `2027-01-05`.

## Guarded transaction

P1-C infrastructure merged in PR #8. The transaction branch then ran guarded apply **33858563869**, which passed:

- read-only preflight;
- exact six-source apply;
- source-registry-only working-diff enforcement;
- canonical/monitor protected-file checks;
- registry validation;
- full unit suite;
- Python compilation;
- browser JavaScript checks;
- derived-site build; and
- guarded registry commit.

The transaction PR changed exactly `data/sources/registry.json` and merged as **`7848b394d47b0a960200ca1077034ddc45847c2e`**. Temporary write workflow was removed before merge.

## Measured after-state

Independent read-only audit run **33859470953** measured source registry **v1.55 / 223**:

- fully explicit modern governance: **25**;
- sources missing one or more governance fields: **198**;
- **P0 backlog: 0**;
- P1 canonical-dependent backlog: **127**;
- P2 registry-only backlog: **71**;
- missing `canonical_provenance_use`: **188**;
- missing `automated_monitoring_use`: **188**;
- missing `verification_mode`: **198**;
- unique sources used by canonical registry: **151**;
- unique sources used by configured monitor: **5**.

Measured P1-C deltas are therefore exactly six-source reductions:

- fully explicit: **19 → 25** (`+6`);
- missing-any: **204 → 198** (`-6`);
- P1: **133 → 127** (`-6`);
- P2: **71 → 71**;
- missing provenance: **194 → 188** (`-6`);
- missing automation: **194 → 188** (`-6`);
- missing verification: **204 → 198** (`-6`).

## Next bounded research direction

The raw remaining queue is led by held SNB (18), ECB publication surface (11), Bank of England (11), RBA release-schedule surface (11), BEA (10), and two Japan statistical surfaces (8 each). P1-D should not simply consume that ranking. The next cohort is selected for dependency plus active horizon, source-scope integrity, regional breadth and domain diversity.

P1-C is **COMPLETE**. No source gained broader authority from official status, public accessibility, machine readability or successful fetching.

## Invariants

- canonical registry **v0.20 / 669**;
- source registry **v1.55 / 223**;
- monitor expectations **v0.7**;
- automatic canonical commit **CLOSED**;
- Google Calendar writes **OFF**;
- Brazil/TSE and SNB remain held for provenance-scope repair;
- permanent workflow cohort remains six.
