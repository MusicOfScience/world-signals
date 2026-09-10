# WORLD SIGNALS — CM closeout / CN handoff v0.1

**Status:** READY-FOR-FINAL-HEAD-VALIDATION  
**Reference date:** 2026-09-10  
**Exact base main:** `1e4a6bbc8670fc36a452740401461f28e313c031` (merged PR #120)  
**CM materialisation commit:** `aafaa2fb3ffe3acce54e587cb69b5d95bd9d9972`  
**Recovery closeout commit:** `9600b66f3a974b895a0c4771d3edb74b5458083e`

## CM completion

CM is a no-production-population Live contract hardening tranche. Live contract metadata advances to v0.9 while remaining exactly 8 observations / 11 evidence rows / 3 Canonical-linked observations. Every production observation object and evidence object is preserved from merged CL.

The contract now fails closed for correction/retraction chronology and evidence, and for conflicting reports that lack genuine evidence/provider plurality or an explicit factual disagreement description. It does not adjudicate a winner or manufacture consensus.

Guarded transaction run `34441432538` / job `102757107224` passed on the first attempt, including 1,276 tests / 68 historical-prestate skips, all governed validators, derived-state consistency, compilation, seven JavaScript checks, static build, exact production-row invariance, protected-layer nonmutation and bounded final diff.

## Post-CM audit

Read-only cross-layer audit run `34441643238` succeeded on the permanent CM state.

Coverage artifact:
- name: `world-signals-coverage-audit-34441643238`;
- artifact id: `10138137545`;
- digest: `sha256:d8c5c58e3e0c3160c1f8699db655586800ad1b5af247c6cad485aee3726dc38f`.

The population shape remains unchanged, as intended. The audit still reports Europe, Latin America and North America as zero-Live prompts; PIF as one completed Canonical-linked Live observation without an Analysis review; no unused completed same-anchor Analysis target; BARMM as linked to a non-completed occurrence; `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` as Monitor prompts; and `CORPORATE_FINANCIAL_MARKET_STRUCTURE` as an Analysis prompt. None of these prompts authorises automatic filling.

## CN selection

`data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md` selects **CN — Brazil fuel-policy Live broadening** for fresh design only after CM is merged.

The selection is based on independent cross-domain relevance rather than quota closure: a 9 September Brazilian federal fuel-policy intervention combines fiscal/tax policy, fuel/commodity shock transmission and government-stated geopolitical context in a currently underrepresented Latin American setting.

CN remains conditional on a fresh post-merge first-party legal-status check. The Finance Ministry announcement supports a bounded policy-development claim, but CN must freshly verify Presidency/Planalto, Diário Oficial and Ministry sources before using stronger legal-effect wording, exact legal identifiers or exact publication/event UTC timing. If the evidence changes materially, CN must revise or abandon the candidate.

Canada–U.S. tariff escalation and EU oil-security context remain credible future Live candidates and are deferred, not discarded.

## Recovery closeout

Temporary recovery helper/workflow:
- `scripts/closeout_cm_docs_tmp.py`;
- `.github/workflows/cm-closeout-docs.yml`.

Closeout workflow run `34442044708` / job `102758938845` succeeded. It:

1. verified exact `origin/main` and merge-base at `1e4a6bbc8670fc36a452740401461f28e313c031`;
2. updated only the human recovery narrative in `ROADMAP.md` and `PROJECT_STATUS.md`;
3. verified mechanically derived current-state consistency;
4. enforced an exact four-path mutation boundary from its trigger head;
5. removed its own helper/workflow before commit;
6. committed recovery state as `9600b66f3a974b895a0c4771d3edb74b5458083e`.

The mechanically derived state block was not hand-edited by the closeout helper.

## Protected boundaries

CM and its closeout do not mutate Canonical, Source Registry, Change Ledger, Monitor configuration/operations, Analysis population, Calendar write authority or OPEC quarantine. Automatic Live ingestion, automatic Monitor→Live, automatic Live→Analysis, automatic Canonical commit and public Live/Analysis projection remain closed.

## Final-head rule

This closeout record intentionally creates a normal repository-authored descendant after the Actions-authored recovery commit. Ordinary CI and coverage must pass on this exact descendant before PR #121 is marked ready for user merge. Earlier green runs are supporting evidence, not substitutes for final-head validation.
