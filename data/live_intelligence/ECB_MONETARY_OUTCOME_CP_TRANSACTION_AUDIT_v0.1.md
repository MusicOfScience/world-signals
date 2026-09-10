# WORLD SIGNALS — ECB monetary-policy outcome CP transaction audit v0.1

**Status:** GUARDED MATERIALISATION COMPLETE / CLOSEOUT VALIDATION IN PROGRESS / USER MERGE REQUIRED  
**Closeout date:** 2026-09-11 Australia/Melbourne  
**ECB event date:** 2026-09-10  
**Exact post-CO base main:** `e1f5c97c183381f7d29bf6957aecd87cacaa96a0`  
**Branch:** `feature/post-co-ecb-monetary-outcome-cp`

## Outcome

CP completes one existing ECB Canonical monetary-policy decision occurrence from first-party outcome evidence and then adds exactly one bounded, primary-confirmed Live outcome linked to that completed occurrence.

Resulting governed state after materialisation:

- Canonical Registry: `v0.43` / **689** occurrences;
- Change Ledger: `v0.29` / **64** entries;
- Live schema/data: `v0.12` / **11** observations / **15** evidence rows / **4** Canonical-linked observations;
- Source Registry: unchanged at `v2.04` / **258** sources;
- Monitor expectations: unchanged at `v0.28` / **26** adapters / **217** explicitly scoped occurrences;
- Analysis: unchanged at **22** reviews / **97** evidence rows / **1** production Live input / **1** production revision;
- automatic Canonical commit: **OFF**;
- Google Calendar write: **OFF**;
- automatic Monitor→Live: **OFF**;
- automatic Live→Analysis: **OFF**;
- public Live observation projection: **OFF**;
- public Live-input projection: **OFF**.

### Canonical lifecycle completion

Existing stable identity preserved:

- occurrence: `WSO-ad4d0618a65059f2`;
- series: `WS.CB.ECB.MONETARY_POLICY_DECISION`;
- canonical name: `ECB Governing Council monetary policy decision — 2026-09-10`;
- schedule source: `WSSRC-CB-003`;
- outcome/completion source family: existing `WSSRC-CB-004`.

CP changes lifecycle from `PLANNED` to `COMPLETED` using the ECB's first-party 10 September monetary-policy decision publication rather than elapsed schedule time.

The stable timing contract is preserved exactly:

- `start_local`: `2026-09-10T14:15:00`;
- `source_timezone`: `Europe/Berlin`;
- `start_utc`: `2026-09-10T12:15:00Z`;
- `time_precision`: `MINUTE`;
- `time_status`: `CONFIRMED`.

The ECB press RSS item for the exact decision URL supplies the publication time `14:15 +0200`, independently matching the pre-existing Canonical decision clock. That agreement corroborates the existing timing; CP does not derive or rewrite the Canonical clock from publication after the fact.

One reviewed Change Ledger entry is appended: `WSCHANGE-e94c7fb7c8d8bd02`, type `LIFECYCLE_COMPLETION`. The transaction generates `committed_at` only at materialisation time; the earlier review timestamp remains separately recorded as `reviewed_at`.

### Live outcome

New observation:

- `WSLI-MON-ECB-RATES-20260910-001`;
- `POLICY_DEVELOPMENT`;
- `PRIMARY_CONFIRMED`;
- region `Europe`;
- jurisdiction `Euro area`;
- `OUTCOME_OF` → completed `WSO-ad4d0618a65059f2`.

New primary-official Live evidence:

- `WSEV-LI-ECB-MP-20260910`;
- provider: European Central Bank;
- exact publication time: `2026-09-10T12:15:00Z` from the ECB press RSS item for the exact decision URL.

The official decision states that the Governing Council raised all three key ECB interest rates by **25 basis points**. From 16 September 2026 the deposit facility rate is **2.50%**, the main refinancing operations rate **2.65%**, and the marginal lending facility rate **2.90%**.

CP records only that official rate decision. It does **not** encode staff projections, expectation/consensus, surprise, market movement, press-conference interpretation, causal attribution or second-order effects. The monetary-policy statement and press conference remain separate evidence/analytical objects rather than additional CP production observations.

## Primary-source recovery

Initial post-release review through normal indexed ECB HTML/search surfaces did not cleanly expose the 10 September decision even after the scheduled release time had passed. CP therefore remained fail-closed and explicitly treated that state as a retrieval/indexing gap rather than evidence that no decision occurred.

A temporary **read-only** GitHub Actions probe, with no governed-write authority, fetched the ECB's own press RSS feed directly. The feed exposed the exact official decision and statement URLs:

- decision: `https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260910~314e508016.en.html`;
- monetary-policy statement: `https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement/2026/html/ecb.is260910~6a45359cfc.en.html`;
- ECB press RSS: `https://www.ecb.europa.eu/rss/press.html`.

The probe then followed those exact first-party URLs and recovered the published decision text and ECB RSS publication metadata. Secondary reporting had indicated a 25 bp hike while the first-party route was temporarily inaccessible, but it was never admitted as Canonical completion evidence or Live production evidence.

The read-only probe workflow was removed before write-capable transaction machinery was introduced.

## Transaction design

CP uses a two-stage semantic transaction within one guarded tranche:

1. **Stage 1 — Canonical lifecycle:** prove direct first-party outcome evidence, preserve the existing identity/timing, materialise `PLANNED → COMPLETED`, append Change Ledger provenance and validate the Canonical state.
2. **Stage 2 — Live outcome:** only against the resulting completed anchor, append one `PRIMARY_CONFIRMED` observation plus one first-party evidence row and validate the Live state.

The executable contract contains a negative test proving Stage 2 refuses an `OUTCOME_OF` link while the anchor remains `PLANNED`. The test constructs an explicit synthetic pre-completion copy so the safety invariant remains valid on legitimate later descendants.

## Pre-write validation

Before any write-capable helper was permitted to materialise governed state, CP passed a full pre-write run at the then-current branch head:

- Canonical validator;
- Live validator;
- Analysis validator;
- derived-state consistency;
- complete historical unittest suite: **1,321 tests passed / 68 historical-prestate skips**;
- Python compilation;
- all seven JavaScript syntax checks;
- static build.

The write helper defaulted to simulation-only and required the explicit environment gate `WORLD_SIGNALS_APPLY_ECB_CP=REVIEWED_APPLY` for materialisation.

## Guarded attempt 1 — historical CO descendant ceiling, failed closed

- workflow run: `34501417118`;
- job: `102952859524`;
- conclusion: **FAILURE**;
- governed transaction committed/pushed: **no**.

Attempt 1 passed exact base/branch checks, protected prestate hashes, pure simulation, focused CP contracts, read-only proof, ephemeral materialisation, derived-state refresh, materialised-target verification, and the Canonical/Live/Analysis validators.

The complete historical suite then failed in two `tests/test_canada_us_counter_tariff_live_co.py` assertions. Both were descendant-state coupling rather than CP payload or validator defects:

1. the CO checkpoint test froze CO's historical `v0.11 / 10 observations / 14 evidence` state as a permanent total-evidence ceiling;
2. the CO simulation test unconditionally applied the exact CO target validator to a legitimate CP `v0.12 / 11 / 15` descendant.

The runner stopped before commit/push. No ephemeral CP governed mutation entered branch history.

### CO descendant repair

Repair commit: `fe84734481907d78178742989c4a2b4cf7a13341`.

Only `tests/test_canada_us_counter_tariff_live_co.py` was changed. Historical CO meaning remains exact:

- the frozen CO checkpoint remains `v0.11 / 10 / 14 / 3 linked`;
- the exact CO observation and its two evidence rows must still equal the frozen CO payload;
- the exact CO validator still runs when the repository is at the CO target version;
- later reviewed descendants may grow the total store while the main Live validator proves current-state validity.

No CO payload, production row, validator, governed data, CM correction/conflict contract or OPEC quarantine material was weakened.

## Guarded attempt 2 — semantic/regression gates green, cleanup bookkeeping failed closed

- workflow run: `34502115902`;
- job: `102955187706`;
- conclusion: **FAILURE**;
- governed transaction committed/pushed: **no**.

Attempt 2 passed:

- exact base/branch checks;
- prestate/protected hashes;
- simulation and focused contracts;
- ephemeral materialisation;
- derived-state refresh;
- Canonical, Live and Analysis validators;
- complete **1,321-test** historical suite / 68 historical-prestate skips;
- Python compilation;
- seven JavaScript checks;
- static build;
- protected-layer and exact pre-CP-row preservation;
- final remote base/branch recheck.

It then failed at the bounded-diff cleanup proof. The workflow had correctly staged deletion of the temporary writer with `git rm`, but enumerated only the unstaged working-tree diff with `git diff --name-only`. The staged writer deletion was therefore invisible to the assertion, which incorrectly reported the required deletion as missing.

The allowed and required transaction path sets were **not** loosened. The fix changed the enumeration to `git diff --name-only HEAD`, which correctly sees both staged and unstaged changes relative to the committed head. Commit/push remained skipped in attempt 2, so no governed state entered branch history.

## Guarded attempt 3 — successful materialisation

- workflow run: `34502339341`;
- job: `102955933422`;
- trigger head: `5ae72f5aa06276bef4a712ce810483868dcd4e2b`;
- materialisation commit: `1986c9cb62396c2a8c036c3b2f65441c5cfdc98b`;
- conclusion: **SUCCESS**;
- transaction artifact: `10162380654`;
- artifact digest: `sha256:fc0fbc81325b0291a5e3b8d9a09ab761ff938b7355f3495fbb6153564d5e8884`.

Attempt 3 passed every guarded step:

- exact post-CO `main` and merge-base gate;
- exact branch-parent/remote-head gate;
- protected-layer and exact pre-CP governed snapshots;
- pure CP simulation;
- focused CP contracts;
- proof that simulation was read-only;
- reviewed ephemeral Stage 1 + Stage 2 materialisation;
- mechanically derived recovery-state refresh;
- exact materialised-target verification;
- Canonical validator;
- Live validator;
- Analysis validator;
- derived-state consistency;
- complete historical suite: **1,321 tests passed / 68 historical-prestate skips**;
- Python compilation;
- all seven JavaScript syntax checks;
- static build;
- protected-layer byte-hash invariance;
- exact preservation of every non-target Canonical occurrence;
- exact preservation of the ECB occurrence's native/local/UTC timing fields;
- exact append-only +1 Change Ledger row;
- exact append-only +1 Live observation / +1 Live evidence row;
- final remote-base and remote-branch recheck;
- temporary Python writer removal;
- bounded transaction diff including the staged writer deletion;
- guarded commit and push;
- transaction artifact upload.

## Cleanup

The transaction commit removed `scripts/apply_ecb_monetary_outcome_cp.py` before it entered the materialised descendant.

The one-shot guarded workflow was then removed through the authenticated GitHub connector because a running workflow cannot safely remove its own definition and continue. Cleanup commit:

- `a881075d37bc224d9be0aad4f922af8b40c5bd43` — `CP: remove temporary guarded transaction workflow`.

A direct repository check after materialisation confirmed the temporary Python writer is absent. Workflow enumeration after materialisation found only the one CP guarded workflow as temporary residue; the cleanup commit removes it.

## Preliminary cleaned-head validation

The first cleaned descendant `a881075d37bc224d9be0aad4f922af8b40c5bd43` passed:

- ordinary PR validation run `34502451870`;
- read-only coverage run `34502451909`;
- coverage artifact `10162410474`;
- coverage artifact digest `sha256:425d981abc8309ff9d31921876f3129659365f9927e194a92834aea67434b238`.

These runs are **historical only** once this permanent audit and the post-CP pressure record are committed. Merge authority requires fresh validation on the actual final head.

## Protected-layer result

CP does not mutate:

- Canonical schema;
- Source Registry;
- Monitor expectations or operations policy;
- Analysis schema, reviews or evidence registry;
- Calendar state;
- OPEC quarantine record or OPEC quarantine regression test.

The only governed Canonical population change is the reviewed lifecycle/provenance update to existing occurrence `WSO-ad4d0618a65059f2`. The only Change Ledger growth is its one reviewed lifecycle entry. The only Live population growth is one observation and one evidence row. The biosecurity overlay changes only its mechanically required Canonical checkpoint alignment; its semantics are preserved.

## Post-CP pressure boundary

The cleaned-head cross-layer audit reports 11 Live observations / 4 Canonical-linked. Two completed linked observations have no Analysis review: the PIF partner-framework outcome and the new ECB rate decision. There are **zero** completed linked observations with an existing Analysis target waiting to consume a Live input.

That state does not authorise a second production Live→Analysis link. Creating an ECB or PIF Analysis review merely to complete the graph would invert the evidence-first architecture. A future ECB analysis may be independently worthwhile, but it requires a fresh analytical question, expectation benchmark/evidence where relevant, market-measurement evidence if market movement is examined, alternatives/noise discipline and a fresh bridge-policy decision.

No next tranche is authorised by this transaction audit. The separate post-CP pressure record governs that closeout decision.

## Handoff boundary

The user performs the merge. The assistant does not.

A merge handoff remains `DO NOT MERGE` until the permanent closeout records are committed and ordinary CI plus read-only coverage pass on the exact final PR head with no temporary workflow/helper residue. Only then may the handoff change to `MERGE NOW`.
