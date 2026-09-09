# WORLD SIGNALS — BARMM pre-election Live CG transaction audit v0.1

**Tranche:** CG  
**Reference date:** 2026-09-10  
**Base main:** `6c96794cb553c6b34df93536141340c2af8db44a`  
**Branch:** `feature/post-cf-live-pressure-cg`

## 1. Governed objective

CG exercises the production Live Intelligence `CONTEXT_FOR` relationship with one current, first-party, pre-election institutional-development observation tied to the already-governed BARMM parliamentary election occurrence `WSO-EL-PH-BARMM-20260914`.

The transaction does **not** alter Canonical event identity, timing, lifecycle, certainty or provenance. It does not add a Monitor route, activate the validated CF NHC pilot, create an Analysis revision, add a second production Live→Analysis input, or change either global write gate.

The quarantined CE OPEC transaction is explicitly excluded from CG selection and implementation. `OPEC_QUARANTINE.md`, closed/unmerged PR #113 and the quarantine regression remain intact.

## 2. Current source and rights review

Selected first-party evidence:

- Philippine Information Agency, 9 September 2026, `GPH-MILF forge commitment to promote peaceful electoral process during the BARMM polls`;
- URL: `https://pia.gov.ph/news/gph-milf-forge-commitment-to-promote-peaceful-electoral-process-during-the-barmm-polls/`.

The article reports government representatives, MILF ground commanders and other stakeholders signing ceasefire-related coordination guidelines and a pledge to promote a peaceful electoral process ahead of the 14 September BARMM parliamentary election.

The article describes the signing as having occurred `recently` but does not establish a source-native exact date or clock time for that act. CG therefore does not create `event_time` from the publication date or from an invented transaction clock.

PIA's current About surface states that its content is in the public domain unless otherwise stated. CG nevertheless stores only the minimum factual/provenance metadata and source URL rather than mirroring page content.

A separate PIA energy-security article published 9 September states the poll date as 15 September. That conflicts with the existing COMELEC-governed 14 September Canonical date and with the selected PIA peace-process article. CG records the disagreement in the pressure audit, rejects the conflicting article as timing authority and does not let Live evidence modify Canonical timing.

## 3. Pre-state

Verified immediately before CG:

- Canonical Registry: `v0.41 / 689`;
- Source Registry: `v2.02 / 257`;
- Monitor expectations: `v0.27 / 25` configured adapters;
- Live Intelligence: `v0.6 / 6` observations / `9` evidence rows;
- Analysis: schema `0.8`, reviews `v0.18 / 22`, evidence `v0.18 / 97`;
- production Analysis revisions: `1`;
- production Live→Analysis inputs: `1`.

The selected Canonical occurrence remained:

- series `WSER-EL-PH-BARMM-PE`;
- `CIVIL_DATE` `2026-09-14`;
- native timezone `Asia/Manila`;
- `start_utc = null`;
- lifecycle `PLANNED`;
- certainty `CONFIRMED`.

## 4. Authorized mutation

Authorized governed writes were limited to:

- `data/live_intelligence/schema.json`;
- `data/live_intelligence/observations.json`;
- `data/live_intelligence/evidence_registry.json`.

CG additionally repairs a narrow set of historical regression tests whose old assertions incorrectly treated the BF `v0.6 / 6 / 9` Live checkpoint as the permanent current head. The repairs preserve historical BF/CD identities and checkpoints while permitting later reviewed descendants.

No assertion was monkey-patched, neutralized or converted to a no-op. The tests continue to check historical membership/identity, closed gates and minimum descendant floors.

## 5. Failed gated attempt 1

**Run:** `34380149895`  
**Job:** `102562730980`  
**Result:** failed before materialisation.

Cause: the first CG preflight assumed a nested Canonical timing object. The production registry stores the target occurrence's timing fields in the flattened canonical record shape (`timing_type`, `start_local`, `source_timezone`, `start_utc`).

Repair: align the CG harness and regression with the production Canonical field layout while retaining the required civil-date, native-timezone and null-UTC invariants.

The materialisation step did not run. The commit gate did not run. No governed state was pushed.

## 6. Failed gated attempt 2

**Run:** `34380340210`  
**Job:** `102563350137`  
**Result:** materialised only inside the ephemeral runner, passed the three primary validators, then failed the full historical regression suite before the commit gate.

Validator state reached in the runner:

- Canonical: `689` PASS;
- Live: schema `0.7`, observations `7`, evidence `10` PASS;
- Analysis: reviews `22`, evidence `97` PASS.

Seven historical tests failed because they froze the current Live head at BF's `v0.6 / 6 / 9` checkpoint or required the BF maximum population forever:

1. `tests/test_bwc_wg8_first_analysis_revision_cd.py`;
2. `tests/test_eurostat_monitor_bk.py`;
3. `tests/test_fomc_monitor_readiness_bm.py`;
4. `tests/test_japan_household_spending_monitor_bl.py`;
5. `tests/test_opec_official_confirmation_bg.py`;
6. `tests/test_un_correct_map_live_bf.py` current-head assertion;
7. `tests/test_un_correct_map_live_bf.py` BF population-ceiling assertion.

Repair: make those current-head checks descendant-safe while preserving their historical semantics. BF's original observation and evidence remain explicitly checked by stable IDs and exact payload membership; later tests retain closed automation/public gates and numerical version/population floors. The historical OPEC BG test change is limited to removing the false permanent Live ceiling; no OPEC provenance or CE transaction machinery is changed.

The commit gate was skipped. The runner materialisation was ephemeral. No governed mutation was pushed from this failed run.

## 7. Successful guarded transaction

**Run:** `34380735933`  
**Job:** `102564666024`  
**Result:** SUCCESS.

Preflight:

- exact `origin/main` remained `6c96794cb553c6b34df93536141340c2af8db44a`;
- merge-base remained the exact CF handover boundary;
- CG simulation returned `CG_SIMULATION_VALID` for exactly one `CONTEXT_FOR` link;
- CG-specific tests: `5/5` PASS;
- OPEC quarantine regressions: `2/2` PASS.

Materialisation:

- actual World Signals observation timestamp: `2026-09-09T17:05:16Z`;
- verdict: `CG_MATERIALIZED_REVIEWED_LIVE_CONTEXT`.

Primary validation:

- Canonical validator: `689` PASS;
- Live validator: schema `0.7`, observations `7`, evidence `10`, population `CONTROLLED_INSTITUTIONAL_SPECIMEN` PASS;
- Analysis validator: reviews `22`, evidence `97`, Live-input bridge and Analysis revision contract PASS.

Full validation:

- unit tests: `1221` run, `OK`, `68` skipped historical-state tests;
- Python compilation: scripts, source adapters and tests PASS;
- JavaScript syntax: app, horizon, native calendar, history, operations, biosecurity and analysis modules PASS;
- static site build PASS for `689` Canonical events, `25` configured Monitor routes, `257` governed sources, Live `0.7`, `22` Analysis reviews;
- generated `docs/`, `site/` and `artifacts/` residue removed before commit.

Protected-hash audit passed unchanged for:

- Canonical registry and schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- Monitor expectations and operations policy;
- Analysis schema, reviews and evidence;
- `OPEC_QUARANTINE.md`;
- `tests/test_opec_quarantine_cf.py`.

`origin/main` was rechecked immediately before commit and still matched the exact CF base.

Guarded materialisation commit:

- commit: `5f9b1e8` (`CG: add reviewed BARMM pre-election Live context`).

## 8. Post-state

Governed state after CG materialisation:

- Canonical Registry remains `v0.41 / 689`;
- Source Registry remains `v2.02 / 257`;
- Monitor expectations remain `v0.27 / 25` configured adapters;
- the CF NHC pilot remains validated but unregistered in scheduled Monitor expectations;
- Live Intelligence becomes `v0.7 / 7` observations / `10` evidence rows;
- reviewed Canonical-linked Live observations become `2`, with CG exercising the first production `CONTEXT_FOR` relationship;
- Analysis remains `22 / 97`, with one production revision and one production Live→Analysis input;
- automatic Canonical commit remains OFF;
- Google Calendar writes remain OFF;
- public Live observation projection remains OFF;
- automatic Live ingestion remains OFF.

The new Live observation is factual context only. It does not assert that the coordination guarantees a peaceful election, changes electoral integrity, predicts the result, resolves the Bangsamoro peace process or causes any market effect.

## 9. Closeout requirement

Before PR handoff, the temporary CG write-capable GitHub Actions workflow and the temporary descendant-repair helper must be removed. The final branch-vs-main diff must contain no generated site/artifact residue and no live CE/OPEC transaction machinery.
