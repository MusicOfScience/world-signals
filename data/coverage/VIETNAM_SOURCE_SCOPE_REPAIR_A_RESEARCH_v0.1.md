# WORLD SIGNALS — Vietnam source-scope repair A research v0.1

**Reference date:** 2026-09-05  
**Repository checkpoint:** `59974424f61f62f3f54c5629b87846bb337b006c`  
**Canonical registry:** v0.21 / 669  
**Source registry:** v1.62 / 224  
**Change ledger:** v0.10  
**Monitor expectations:** v0.7  
**Scope:** repair the provenance of the one Vietnam National Assembly occurrence currently attached to Government Electronic Newspaper source `WSSRC-REG5-001`, without changing its date, certainty, lifecycle or stable identity.

## Why this is a source-scope repair

Verification Closeout A deliberately held `WSSRC-REG5-001` out because the registered source is official but one institutional step removed from the event itself. The current source identity is the Government Information and Communication Department / Government Electronic Newspaper, reporting on the National Assembly Standing Committee's preliminary programme.

Current first-order evidence is available from the National Assembly of Vietnam's own electronic portal. Ordinary verification-mode backfill would therefore make the existing secondary provenance look complete without resolving the source hierarchy.

The project charter requires primary issuing-institution provenance where available and stable source identities. The correct response is to preserve the existing Government Electronic Newspaper source as a secondary official source, create a distinct National Assembly source identity, and reassign only the affected canonical occurrence.

## Read-only repository diagnostic

Temporary read-only run `33908970268` was executed from exact merged PR #27 checkpoint `59974424f61f62f3f54c5629b87846bb337b006c`.

It found exactly **one** canonical dependency on `WSSRC-REG5-001`:

- `WSO-REG-G-0001` — **Vietnam 16th National Assembly — Second Session opening**.

The occurrence currently stores:

- `series_id = WSER-REG5-VN-NA-SESSION`;
- `institution = National Assembly of Vietnam`;
- `certainty_status = PROVISIONAL`;
- `activation_mode = PROVISIONAL_OFFICIAL_PROGRAMME`;
- `lifecycle_status = PLANNED`;
- `start_local = 2026-10-20`;
- `time_precision = DAY`;
- `source_timezone = Asia/Ho_Chi_Minh`;
- phase 1 metadata `2026-10-20` through `2026-11-13`, PROVISIONAL;
- phase 2 metadata `2026-11-25` through `2026-12-05`, PROVISIONAL;
- current source assertion `WSA-edffdbb284fcbfd9`.

No other canonical record is authorised to change in this repair.

## First-order National Assembly evidence

Direct National Assembly portal article:

https://quochoi.vn/tintuc/Pages/tin-hoat-dong-cua-quoc-hoi.aspx?ItemID=99777

The National Assembly portal identifies the governing authority of the portal as the **National Assembly of the Socialist Republic of Vietnam**. In its 11 May 2026 report on initial preparation for the second session of the 16th National Assembly, it states that the National Assembly Standing Committee basically agreed the preliminary programme and that the regular year-end second session was expected to open on **20 October 2026** at the National Assembly House.

The direct National Assembly article therefore supplies the same provisional opening date currently stored in WORLD SIGNALS, while being institutionally closer to the event than the Government Electronic Newspaper report.

The Government Electronic Newspaper article remains useful secondary official corroboration:

https://baochinhphu.vn/chuan-bi-ky-luong-tu-som-ky-hop-thu-2-quoc-hoi-khoa-xvi-102260511145333161.htm

It additionally reports the preliminary two-block programme:

- phase 1: 20 October–13 November 2026;
- phase 2: 25 November–5 December 2026.

Those phase windows remain metadata and remain **PROVISIONAL**. The repair does not promote them to confirmed timing.

## Source identity decision

Do **not** repurpose `WSSRC-REG5-001`.

That stable source ID explicitly identifies the Government Information and Communication Department / Government Electronic Newspaper. Changing its institution and URL to the National Assembly portal would erase the historical provenance identity that originally supported the occurrence.

Create a new source:

- `WSSRC-REG5-002` — National Assembly of Vietnam / National Assembly Electronic Portal.

After repair:

- `WSSRC-REG5-002` is the primary canonical provenance source for `WSO-REG-G-0001`;
- `WSSRC-REG5-001` remains an official secondary/corroborating source with zero derived canonical dependencies;
- no duplicate canonical occurrence is created.

This mirrors the earlier Brazil provenance decomposition: distinct institutional authorities receive distinct source identities rather than being collapsed into one composite source.

## Rights and automation classification

The National Assembly portal is clearly first-order official authority. The current review did **not** identify a specific general reuse licence or a grant of automated retrieval rights for the portal.

This distinction matters:

- authority is sufficient to use the page as a manual provenance reference for the minimal factual schedule metadata;
- public web accessibility is not a production polling licence;
- no crawler, parser or live-monitor route is authorised by this repair.

Frozen conservative classification for `WSSRC-REG5-002`:

- `canonical_provenance_use = MANUAL_INFORMATIONAL_REFERENCE_ONLY`;
- `automated_monitoring_use = PROHIBITED_OR_RIGHTS_HOLD`;
- `verification_mode = RIGHTS_HELD_MANUAL_ONLY`;
- `monitoring_readiness_status = RIGHTS_AUDIT_REQUIRED`;
- `monitoring_activation_status = MANUAL_AUTHORITATIVE_RECHECK_ONLY`.

The existing Government Electronic Newspaper source already has an explicit republication/source-attribution notice and curated-factual-metadata clearance. Once it becomes secondary provenance, its missing verification mode can be resolved conservatively as:

- `verification_mode = MANUAL_AUTHORITATIVE_RECHECK`;
- automated monitoring remains `ENDPOINT_REVIEW_REQUIRED`.

This is an operational source-governance classification, not legal advice.

## Canonical repair — one occurrence only

`WSO-REG-G-0001` remains the same stable occurrence with the same series, date, status and session-phase metadata.

Only provenance-semantic fields are authorised to change:

- `source_id`: `WSSRC-REG5-001` → `WSSRC-REG5-002`;
- `primary_source_assertion_id`: `WSA-edffdbb284fcbfd9` → `WSA-6b2aa27a0df846dc`;
- `last_successful_assertion_id`: same new assertion ID;
- `last_verified_at`: refresh to `2026-09-05`.

The institution field is already correctly `National Assembly of Vietnam` and does not change.

The deterministic assertion ID is recomputed because source identity is part of assertion identity. Its frozen post-repair value is `WSA-6b2aa27a0df846dc`.

The following must remain unchanged:

- occurrence ID `WSO-REG-G-0001`;
- series ID `WSER-REG5-VN-NA-SESSION`;
- canonical and calendar titles;
- institution `National Assembly of Vietnam`;
- `start_local = 2026-10-20`;
- civil-date/day/all-day semantics;
- `Asia/Ho_Chi_Minh` source timezone;
- `PROVISIONAL` certainty/time status;
- `PROVISIONAL_OFFICIAL_PROGRAMME` activation/time basis;
- lifecycle `PLANNED`;
- both provisional phase windows;
- importance, sensitivity, transmission-channel and render-policy fields.

Canonical version may advance **v0.21 → v0.22** because provenance semantics change; canonical count remains **669**.

## Transaction boundary

A later guarded transaction, and only that transaction, may alter:

1. `data/canonical/registry.json` — one occurrence's provenance fields; no timing change and count unchanged;
2. `data/sources/registry.json` — retain/update `WSSRC-REG5-001`, append `WSSRC-REG5-002`, advance source registry to v1.63 / 225;
3. `data/changes/ledger.json` — append one reviewed provenance-scope repair entry and advance ledger v0.10 → v0.11; `committed_at` is generated at transaction time;
4. `data/coverage/biosecurity_overlay.json` — advance only its pinned canonical checkpoint from v0.21 / 669 to v0.22 / 669.

The transaction must leave monitor expectations and live-monitor code byte-identical, keep automatic canonical commit false, keep Google Calendar writes false, preserve all 669 occurrence IDs and preserve every canonical date/time.

No ordinary 88-P1 tranche is authorised by this repair.
