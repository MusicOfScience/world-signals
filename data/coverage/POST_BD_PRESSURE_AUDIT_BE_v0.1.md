# WORLD SIGNALS — post-BD pressure audit BE v0.1

**Reference date:** 2026-09-07  
**Exact post-BD main base:** `e54dddbaa0d60a39babc2fa47c1f054954b5c9ac`  
**Decision:** bounded OPEC+ lifecycle completion using reputable-newswire fallback, with primary provenance explicitly pending

## Why another population step is not automatic

BD completed the fifth controlled Live Intelligence specimen and left four downstream gates closed: a sixth Live observation, broader ingestion, a second production Live→Analysis relationship and a first production Analysis revision. Those closed gates are not a queue of work. BE begins with a fresh pressure audit across upstream and downstream layers.

The immediate 5–10 September Canonical window contains 19 occurrences. At the BE review point, the 6 September OPEC+ voluntary-adjustment review is the only clearly elapsed high-sensitivity occurrence in that window with competent current reporting that the scheduled event occurred. The 7–10 September items are current or future in their source-native calendars/timezones and are not promoted to post-event state merely because Melbourne has crossed a civil-date boundary.

## Existing governed OPEC identity

The event already exists in Canonical:

- occurrence: `WSO-COM-A-0001`
- series: `WSER-COM-OPEC-VOL`
- Canonical name: **OPEC+ voluntary-adjustment review — seven participating countries**
- schedule source: `WSSRC-COM-001`
- start: `2026-09-06`
- timing: `CIVIL_DATE` / `DAY`
- UTC: `null`
- certainty: `CONFIRMED`
- lifecycle before BE: `PLANNED`
- intrinsic importance: `HIGH`
- expected market sensitivity: `HIGH`

BE therefore must update the stable existing occurrence if completion is defensible. It must not create a duplicate summit/meeting occurrence.

## Source hierarchy and the primary-source problem

The competent primary source remains OPEC. The governed OPEC source `WSSRC-COM-001` is manually curated because OPEC website reuse/database rights are held from production automation. It remains the schedule/decision authority and is not displaced by BE.

Current research established:

1. OPEC's 2 August 2026 official notice explicitly scheduled the next voluntary-adjustment review for **6 September 2026**: `https://www.opec.org/pr-detail/611-2-august-2026.html`.
2. The accessible/indexed OPEC press-release surface available during BE research did not expose the 6 September outcome statement: `https://www.opec.org/press-releases.html`.
3. This indexing/access result is **not** evidence that OPEC failed to issue a statement.
4. Reuters reported on 6 September that the seven-country group met and kept October output policy unchanged, explicitly attributing the decision to a group statement: `https://www.reuters.com/business/energy/opec-set-keep-oil-output-policy-unchanged-sunday-sources-say-2026-09-06/`.

The Charter's source hierarchy permits a highly reputable newswire when primary material is unavailable. That fallback does not become equivalent to primary provenance. BE therefore separates two propositions:

- **event completion:** sufficiently supported for a reviewed lifecycle update;
- **ideal primary outcome provenance:** still pending and must be upgraded when the OPEC statement becomes retrievable.

## Competing pressures

### 1. OPEC 6 September lifecycle completion — SELECTED

This is an upstream state defect: a high-importance scheduled occurrence has occurred according to current post-event reporting but remains `PLANNED`. Correcting lifecycle before downstream population preserves the project architecture.

A repository readiness simulation shows that changing only this occurrence to `COMPLETED` raises completed Analysis-eligible occurrences from **21 to 22** while existing reviewed occurrences remain **21**. The resulting one completed/unreviewed anchor is a consequence of upstream truth, not a target to fill.

### 2. Sixth Live Intelligence observation — HELD

Adding a Live OPEC headline before repairing the scheduled Canonical lifecycle would reverse the intended architecture. BD's fifth-observation ceiling remains a pressure-audit gate, not an invitation to grow the feed.

### 3. Second production Live→Analysis relationship — HELD

AZ remains the sole production Live input. OPEC has no Live observation or reviewed Analysis packet. BE does not create either merely to exercise the bridge a second time.

### 4. First production Analysis revision — HELD

BA established revision grammar but no evidence-driven need to revise an existing reviewed Analysis snapshot has been established here. OPEC is a new completed Canonical anchor, not a revision of an existing analytical judgement.

### 5. Manual Source/Change Monitor review candidate — REJECTED FOR BE

The retained review-state architecture is deliberately a bounded reduction of monitor Actions evidence plus reviewed manual decisions; it is not a permanent general-purpose candidate database. Creating a manual newswire-triggered candidate persistence mechanism solely for OPEC would introduce a new queue architecture when a reviewed Charter-compliant fallback completion is already possible. Automatic Canonical commit remains off.

### 6. Create the Reuters-reported 4 October next meeting — REJECTED

Reuters reports 4 October as the next meeting date. BE does **not** use secondary fallback reporting to create a new future Canonical occurrence. A future OPEC meeting is admitted only when competent authoritative scheduling provenance is independently retrievable and reviewed. This preserves the rule that future events are not confirmed from expectation, custom or a convenient secondary report.

### 7. Upcoming 7–10 September events — HELD

CBD, WHO, Eurostat, Japan, UNGA, Mexico, China, ECB, EIA, APEC, Argentina and other near-term occurrences remain governed by their native schedules and lifecycle evidence. BE does not bulk-complete or pre-emptively populate them.

## BE source object

BE introduces one completion-only source object, `WSSRC-COM-015`, for the Reuters report. It is deliberately constrained:

- secondary reputable newswire, not primary authority;
- zero Canonical dependencies;
- completion-only provenance for `WSO-COM-A-0001`;
- no forward-schedule authority;
- no monitoring route;
- production automated retrieval prohibited in BE;
- minimal factual metadata/link only; no Reuters article text stored;
- primary OPEC provenance upgrade explicitly required when retrievable.

`WSSRC-COM-001` remains unchanged and remains the OPEC schedule/decision authority.

## Canonical mutation boundary

BE may change exactly one existing occurrence and only these lifecycle/provenance fields:

- `lifecycle_status`
- `last_verified_at`
- `last_successful_assertion_id`
- append one `status_history` entry
- append one `related_documents` entry

It must preserve:

- `occurrence_id`
- `series_id`
- `source_id`
- `start_local`
- `start_utc = null`
- `source_timezone = null`
- `timing_type = CIVIL_DATE`
- `time_precision = DAY`
- certainty and importance/sensitivity fields
- all non-target Canonical rows byte/semantic-equivalent apart from registry metadata required by the transaction.

No event clock time is inferred from the Reuters publication time or from any phrase describing when the meeting took place.

## Registry and ledger plan

If preflight is green, target state is:

- Canonical Registry `v0.40 / 689`
- Source Registry `v1.82 / 245`
- Change Ledger `v0.26 / 61`
- biosecurity overlay `v0.15 @ canonical v0.40 / 689`, checkpoint only; semantics unchanged
- monitor expectations unchanged `v0.10 / 8`
- Live unchanged `v0.5 / 5 observations / 7 evidence`
- Analysis unchanged `v0.17 / 21 reviews / 95 evidence`, schema `v0.7`
- completed Analysis-eligible occurrences `22`
- reviewed occurrences `21`
- completed/unreviewed Analysis anchors `1`
- production Live inputs `1`
- production Analysis revisions `0`
- production `EXACT_TIMESTAMP_SERIES` `0`
- automatic Canonical commit OFF
- Google Calendar writes OFF.

Stable planned assertion becomes a reviewed completion assertion `WSA-cddde6887f8083ca`; the reviewed Change Ledger identity is `WSCHANGE-4730a5ef260b271967`.

## Future primary-provenance upgrade

When the competent 6 September OPEC statement becomes retrievable:

1. preserve `WSO-COM-A-0001` and its `COMPLETED` lifecycle;
2. preserve `WSSRC-COM-015` in provenance history rather than pretending the fallback was never used;
3. add or link the primary OPEC outcome evidence through a separate reviewed provenance change;
4. if the primary source conflicts materially with the fallback proposition, open a new reviewed correction/change rather than silently rewriting history;
5. do not automatically create the next occurrence from the primary statement unless its schedule claim is separately admitted under the normal future-event rules.

## Decision

**Proceed to read-only preflight for a bounded OPEC fallback lifecycle completion.**

This is not permission for broader secondary-source lifecycle completion. BE is a single pressure-audited exception using the Charter's explicit fallback tier because the event is already Canonical, the scheduled identity is stable, post-event occurrence is strongly supported, and the primary provenance gap is explicitly retained rather than concealed.
