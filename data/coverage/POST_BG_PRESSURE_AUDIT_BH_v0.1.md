# WORLD SIGNALS — post-BG pressure audit BH v0.1

**Reference date:** 2026-09-08  
**Exact post-BG main base:** `eb0845c791133bb8262692c8ebe38ab362dfeff1`  
**Decision:** recover competent OPEC-primary outcome provenance for the already-completed 6 September 2026 voluntary-adjustment review; population effect none.

## 1. Recovered post-BG checkpoint

Current `main` was reverified before BH planning at `eb0845c791133bb8262692c8ebe38ab362dfeff1`, the merge commit for PR #88. The current override and governed files remain:

- Canonical Registry `v0.41 / 689`;
- Canonical schema `v0.52`;
- Source Registry `v1.83 / 246`;
- Change Ledger `v0.27 / 62`;
- biosecurity overlay `v0.16 @ Canonical v0.41 / 689`;
- monitor expectations `v0.10 / 8 adapters` and operations policy `v0.1`;
- Live Intelligence `v0.6 / 6 observations / 9 evidence`, public projection closed;
- Analysis `v0.17 / 21 reviews / 95 evidence`, one production `live_input`, zero production revisions and zero production `EXACT_TIMESTAMP_SERIES`;
- one completed/unreviewed Analysis-eligible occurrence, `WSO-COM-A-0001`, explicitly not a population target;
- automatic Canonical commit OFF and Google Calendar writes OFF.

The latest scheduled read-only monitor run inspected during recovery was run `34111609049` (run 83). All eight configured adapters were healthy, there were zero review candidates, Canonical was byte-unchanged, and both automatic Canonical commit and Google Calendar write remained false. No monitor/auto-commit pressure is selected.

Exactly the six permanent workflows remain on current `main`; no BF/BG temporary write-capable workflow survives.

## 2. Material post-BG evidence change

BG deliberately stopped short of claiming competent OPEC-primary outcome provenance. It retained:

- `WSSRC-COM-001` as the competent OPEC schedule/decision authority;
- Reuters `WSSRC-COM-015` as the historical BE completion fallback;
- SPA `WSSRC-COM-016` as official participating-government confirmation only;
- the OPEC-primary provenance requirement as `REQUIRED_WHEN_RETRIEVABLE`.

That retrieval condition has now changed materially.

The competent OPEC issuing institution now exposes an official press release at:

`https://www.opec.org/pr-detail/613-6-september-2026.html`

Title: **Saudi Arabia, Russia, Iraq, Kuwait, Kazakhstan, Algeria, and Oman reaffirm commitment to market stability**.

The OPEC release states that the seven participating OPEC+ countries met virtually on **6 September 2026**, reviewed global market conditions and outlook, decided to maintain September 2026 required production for October 2026, reiterated conformity commitments, and would continue monthly review meetings.

This is the evidence class BG explicitly required when retrievable: competent issuing-institution outcome provenance. It is stronger for the governed OPEC assertion than both Reuters fallback and SPA participating-government confirmation.

The OPEC page does not establish a canonical clock time for the meeting. BH therefore retains `CIVIL_DATE` / `2026-09-06`, `start_utc = null` and no source timezone for event time. No publication timestamp is promoted into event time.

## 3. Competing post-BG pressures

### A. Monitor / automatic Canonical commit — defer

Run 83 is empirically `NO_CHANGE`: eight healthy adapters, zero candidates, Canonical unchanged. There is no reschedule/cancellation specimen with which to test a write gate. Route health is not automation permission.

### B. Standalone OPEC Analysis review — defer behind upstream provenance repair

`WSO-COM-A-0001` remains the sole completed/unreviewed Analysis-eligible occurrence, but queue status is not a target. The newly retrievable OPEC primary outcome materially improves the upstream Canonical provenance contract and should be repaired before deciding whether a separate Analysis packet is justified. BH makes no observed-market-response or causality claim.

### C. Second production Live → Analysis link — keep closed

No independently selected Analysis problem requires a second bridge relationship. AZ remains the sole production `live_input`; bridge growth is not a quota.

### D. First production Analysis revision — keep closed

No reviewed Analysis snapshot has acquired a demonstrated judgement-changing evidence delta requiring revision. BA grammar existence is not a production reason.

### E. Seventh Live observation / new geographic specimen — not selected

Fresh official surfaces were checked across Australia, ASEAN and African Union material. They contain potentially useful policy, institutional and schedule developments, but none creates a stronger current contract pressure than the exact provenance debt already encoded by BE/BG. Geographic diagnostics remain prompts, not quotas.

### F. OPEC competent-primary provenance recovery — selected

This is the strongest current pressure because it closes an explicit, bounded, already-governed source-hierarchy debt using newly retrievable first-order evidence, with no population growth and no need to exercise a downstream gate merely because it exists.

## 4. BH selected contract

BH may:

1. preserve stable occurrence `WSO-COM-A-0001` and series `WSER-COM-OPEC-VOL`;
2. reuse existing competent source identity `WSSRC-COM-001` rather than create a duplicate OPEC source object;
3. append one exact OPEC outcome locator as competent-primary supporting provenance;
4. advance the occurrence's latest successful reviewed assertion to a new BH assertion;
5. add exactly one reviewed Change Ledger entry recording competent-primary provenance recovery;
6. advance Canonical/ledger versions and the biosecurity-overlay Canonical checkpoint only as required by governed version coupling;
7. update `PROJECT_STATUS.md` and `ROADMAP.md` to mark the OPEC-primary gap satisfied;
8. narrowly harden the historical BG regression harness so BG's exact checkpoint remains frozen without making its old latest-assertion value a descendant ceiling.

BH must **not**:

- alter lifecycle (`COMPLETED` remains `COMPLETED`), certainty, date, time precision, category, event type, stable identities, importance or expected sensitivity;
- rewrite BE Reuters or BG SPA historical provenance rows;
- delete their source objects;
- treat OPEC publication metadata as event time;
- create a 4 October occurrence from the outcome page;
- mutate monitor configuration, Live Intelligence or Analysis populations;
- create an Analysis review, second Live → Analysis link or Analysis revision;
- infer observed market impact or causal transmission;
- open automatic Canonical commit or Google Calendar writes.

## 5. Target state

If controlled materialisation succeeds:

- Canonical Registry `v0.42 / 689`;
- Source Registry `v1.83 / 246`, unchanged;
- Change Ledger `v0.28 / 63`;
- biosecurity overlay `v0.17 @ Canonical v0.42 / 689`, semantic overlay unchanged;
- monitor expectations `v0.10 / 8`, unchanged;
- Live Intelligence `v0.6 / 6 / 9`, unchanged and public projection closed;
- Analysis `v0.17 / 21 / 95`, unchanged;
- production `live_inputs` 1;
- production Analysis revisions 0;
- production `EXACT_TIMESTAMP_SERIES` 0;
- automatic Canonical commit OFF;
- Google Calendar writes OFF.

The completed/unreviewed Analysis anchor remains one. Provenance repair does not compel Analysis population.

## 6. Historical/descendant contract

BE's Reuters fallback and BG's SPA confirmation remain auditable facts about what evidence was available and used at those checkpoints. Their historical `REQUIRED_WHEN_RETRIEVABLE` markers are not rewritten. BH adds the later competent OPEC evidence that satisfies the requirement.

BG's historical exact post-state remains `v0.41 / 689`, Source `v1.83 / 246`, Ledger `v0.27 / 62`. Tests must preserve those checkpoint assertions while accepting legitimate reviewed descendants in which a later assertion becomes the current `last_successful_assertion_id`.

## 7. Decision

Proceed with a bounded, population-neutral BH competent-OPEC-primary provenance transaction. Do not bundle OPEC Analysis, bridge growth, Analysis revision, Live population, monitor expansion or calendar population into BH.
