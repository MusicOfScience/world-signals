# WORLD SIGNALS — UN Correct Map Live BF transaction audit v0.1

**Tranche:** BF  
**Transaction run ID:** `34049594202`  
**Exact post-BE main base SHA:** `629ab595ecccaf86a92bbd8cdfdab4297496b298`  
**BF branch transaction-start SHA:** `bb04298377658a2fc6fb3b5697f10941fa5be248`  
**Temporary workflow activation SHA:** `aa5532409b79bb7a7aaf819bc34fff1a2cce3045`  
**Successful preflight run:** `34043141267` — SUCCESS  
**Transaction materialisation commit:** PENDING_LOCAL_COMMIT  
**Temporary transaction workflow removal commit:** PENDING_LOCAL_COMMIT

## Decision and provenance

BF implements the reviewed decision in `POST_BE_PRESSURE_AUDIT_BF_v0.1.md`: add exactly one sixth controlled Live Intelligence specimen, an `INSTITUTIONAL_DEVELOPMENT`, without Canonical, Source Registry, Change Ledger, monitor or Analysis mutation.

Primary provenance remains:
- United Nations General Assembly meeting coverage: `https://press.un.org/en/2026/ga12779.doc.htm`;
- African Union Commission communiqué: `https://au.int/en/pressreleases/20260904/communique-auc-chairperson-adoption-correct-map-resolution`.

The institutional record is resolution `A/RES/80/307`, adopted on **4 September 2026** at civil-date precision, by recorded vote **164 in favour, 1 against, 6 abstentions**.

The UN source is authoritative for the General Assembly adoption and vote. The African Union source is contextual/source-confirmation evidence for the Africa-led initiative and Togo/African Group role; it is not promoted to authority for the UN vote count.

## Epistemic boundary

BF records the institutional adoption only. It does **not** claim that the resolution:
- imposes one compulsory world map;
- changes borders, territorial status or sovereignty;
- establishes an economic, political or market consequence;
- proves downstream implementation outcomes.

No event clock time or publication clock time was invented. Event and publication timing remain at `CIVIL_DATE` precision for 4 September 2026.

## Materialised target

- Live Intelligence schema: **v0.6**
- population policy: **CONTROLLED_INSTITUTIONAL_SPECIMEN**
- observations: **6**
- evidence rows: **9**
- maximum observations: **6**
- maximum evidence rows: **9**
- public Live observations: **0**
- automatic ingestion: **CLOSED**
- automatic Canonical commit: **CLOSED**
- Google Calendar writes: **CLOSED**

New observation:
- `WSLI-INST-UNGA-CORRECTMAP-20260904-001`

New evidence:
- `WSEV-LI-UNGA-CORRECTMAP-UN-20260904`
- `WSEV-LI-UNGA-CORRECTMAP-AU-20260904`

## Mutation proof

The governed BF transaction changed exactly:
- `data/live_intelligence/schema.json`
- `data/live_intelligence/observations.json`
- `data/live_intelligence/evidence_registry.json`
- `PROJECT_STATUS.md`
- `ROADMAP.md`

The following protected paths remained byte-identical to the transaction-start state:
- `data/canonical/registry.json`
- `data/canonical/schema.json`
- `data/sources/registry.json`
- `data/changes/ledger.json`
- `data/coverage/biosecurity_overlay.json`
- `data/monitor/expectations.json`
- `data/monitor/operations_policy.json`
- `data/analysis/schema.json`
- `data/analysis/event_reviews.json`
- `data/analysis/evidence_registry.json`

Generated static-site output was treated as validation output and reverted/cleaned before the mutation-boundary proof.

## Validation

- Canonical validator: PASS
- Live Intelligence validator: PASS
- Analysis validator: PASS
- Full suite: `Ran 861 tests in 6.148s; OK (skipped=40)`
- Python compile checks: PASS
- JavaScript syntax checks: PASS
- Static build: PASS — `Built static site for 689 events, 8 configured live monitor routes, 245 governed sources, Live Intelligence 0.6 (CONTROLLED_INSTITUTIONAL_SPECIMEN; 0 public observations), 21 analytical review(s), reviewed change history, biosecurity_overlay=7series/2candidates, runtime=UNAVAILABLE_AT_BUILD and retained_review=UNAVAILABLE_NO_RETAINED_REVIEW_FETCH(0) -> /home/runner/work/world-signals/world-signals/docs`
- Protected-path SHA-256 verification: PASS
- BF governed mutation-boundary proof: PASS
- public Live observation projection: **0 / CLOSED**

## Transaction disposition

The successful BF materialisation is permanent on this branch and is not reset after validation. The temporary transaction workflow is self-removed before the final branch head is pushed. BF remains **manual-merge only**. No auto-merge is authorised or performed.
