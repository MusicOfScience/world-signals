# WORLD SIGNALS — CE OPEC primary provenance research v0.1

**Reference date:** 2026-09-09  
**Exact merged base:** `9552c1db0d212af33524b80b28d91ef7a897e2d8`  
**Target occurrence:** `WSO-COM-A-0001`

## Why CE changes course from the raw pressure ranking

The post-CD architecture pressure audit found Live Intelligence to be the narrowest populated governed layer: six observations, nine evidence rows and only one Canonical-linked occurrence. That ordinarily makes a seventh Live observation the leading next specimen.

Current-source research, however, exposed a higher-priority provenance obligation already encoded in Canonical. BE completed the 6 September OPEC+ voluntary-adjustment review with a Reuters completion-only fallback because the competent OPEC outcome statement was not retrievable at the time. BG then added Saudi Press Agency official participating-government confirmation while explicitly retaining `REQUIRED_WHEN_RETRIEVABLE` for competent OPEC primary provenance.

The competent OPEC outcome statement is now directly retrievable. The charter's source hierarchy therefore requires that known provenance debt be repaired before the same outcome is used to expand a downstream Live layer.

## Current competent primary evidence

OPEC press release:

- provider: Organization of the Petroleum Exporting Countries (OPEC)
- title: *Saudi Arabia, Russia, Iraq, Kuwait, Kazakhstan, Algeria, and Oman reaffirm commitment to market stability*
- locator: `https://www.opec.org/pr-detail/613-6-september-2026.html`
- reviewed 2026-09-09

The statement establishes, at the factual level needed for this transaction, that:

1. Saudi Arabia, Russia, Iraq, Kuwait, Kazakhstan, Algeria and Oman met virtually on 6 September 2026;
2. the seven participating countries decided to maintain September 2026 required production for October 2026;
3. they said they would continue monthly meetings; and
4. the next seven-country meeting was stated for 4 October 2026.

CE uses only items 1–2 to satisfy the existing 6 September occurrence's primary outcome provenance. Item 4 is retained in research only. CE does not create, rename, merge or otherwise alter an October Canonical occurrence. In particular, the seven-country monthly review must not be silently conflated with the separately existing `WSO-COM-A-0002` 68th OPEC+ JMMC meeting merely because both are dated 4 October.

## Time discipline

The reviewed OPEC statement identifies the meeting by civil date. CE does not infer a clock time, timezone or UTC timestamp. The existing Canonical timing remains:

- `start_local = 2026-09-06`
- `start_utc = null`
- `source_timezone = null`
- `timing_type = CIVIL_DATE`
- `time_precision = DAY`

The transaction is provenance strengthening only. It is not a lifecycle update, schedule update or timing repair.

## Source identity and rights boundary

No new Source Registry object is required. `WSSRC-COM-001` is already the governed OPEC official-announcement family and competent schedule/decision authority. CE adds the specific outcome-page locator to the target occurrence as a related document under that existing source identity.

OPEC's current Terms and Conditions permit hyperlinks but place material restrictions on reproduction, redistribution and shared electronic/database storage without written authorization. They also permit occasional attributed use in internal/research reports. CE therefore does **not** change any existing `WSSRC-COM-001` rights, ingestion, automation or monitoring classification.

Rights locator: `https://www.opec.org/terms-and-conditions.html`

The existing source constraints remain operative, including:

- `automated_retrieval_permission = PRODUCTION_HOLD_WRITTEN_AUTHORIZATION_REQUIRED`
- `monitoring_readiness_status = RIGHTS_OR_LICENSE_HOLD`
- manual/occasional research provenance only

The governed data stores only minimal factual metadata, attribution and the source link. It does not store the OPEC page body.

## Historical provenance preservation

CE must preserve the evidence path actually used when the lifecycle changed:

- Reuters `WSSRC-COM-015` remains the BE completion fallback and its related-document object remains unchanged;
- SPA `WSSRC-COM-016` remains the BG supporting official confirmation and its related-document object remains unchanged;
- the BE/BG ledger entries remain immutable;
- the pre-existing status history remains immutable.

A new provenance-only status-history entry and new append-only ledger entry record that the previously pending competent-primary requirement has now been satisfied. Historical fallback provenance is not rewritten as though OPEC primary had been available earlier.

## Bounded CE mutation

CE may change only:

- the existing Canonical occurrence `WSO-COM-A-0001` by adding the competent-primary related document, advancing `last_successful_assertion_id`, advancing `last_verified_at`, and appending a provenance-only status-history row;
- Canonical registry metadata `v0.41 → v0.42` with the population fixed at 689;
- Change Ledger `v0.27 / 62 → v0.28 / 63` by one append-only provenance-strengthening entry;
- biosecurity overlay checkpoint metadata only, `v0.16 @ Canonical 0.41 → v0.17 @ Canonical 0.42`, with overlay semantics unchanged.

CE must not change Sources, Monitor, Live Intelligence, Analysis, event timing, lifecycle/certainty, importance/sensitivity, Calendar state or any automatic-write gate.

## Next pressure candidate

Once this provenance debt is repaired and merged, the architecture pressure result still points toward a separately audited seventh Live Intelligence observation. The 6 September OPEC+ outcome remains a strong candidate because it would broaden Canonical-linked Live coverage from East Asian macro data into global energy/commodities policy. That downstream population decision is deliberately deferred; CE itself stops at the Canonical provenance boundary.
