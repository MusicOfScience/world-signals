#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROADMAP = ROOT / "ROADMAP.md"
STATUS = ROOT / "PROJECT_STATUS.md"


def replace_between(path: Path, start: str, end: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(start) != 1 or text.count(end) != 1:
        raise RuntimeError(f"closeout anchors not unique in {path}")
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(before + replacement + end + after, encoding="utf-8")


roadmap_replacement = '''### Stage 10F — CM Live correction / retraction / conflicting-report contract hardening — DONE / GUARDED

CM starts from exact merged #120 main `1e4a6bbc8670fc36a452740401461f28e313c031` and hardens the executable Live correction/retraction/conflict grammar **without production population**.

Result:

- Live contract metadata advances from v0.8 to **v0.9** while remaining exactly **8 observations / 11 evidence rows / 3 Canonical-linked observations**;
- every production observation and evidence object is preserved exactly from the merged CL base;
- `CORRECTED` / `RETRACTED` now require an explicit prior Live target, `CORRECTION_OR_REVISION` evidence and strictly later `observed_at_utc`;
- `CONFLICTING_REPORTS` now requires at least two unique evidence records from at least two distinct normalised providers plus a factual `conflict_description`;
- Live does not choose a winning source or manufacture consensus from disagreement;
- `DATA_REVISION` remains the separate external-data revision concept and does not require synthetic prior Live history;
- no production conflict/correction/retraction row is added and Waqa Moana remains un-reinterpreted historical pressure evidence;
- automatic ingestion, public Live projection, Canonical/Calendar write and automatic downstream promotion remain closed.

Guarded run `34441432538` / job `102757107224` passed on its first attempt, including **1,276 tests / 68 historical-prestate skips**, all governed validators, derived-state consistency, compilation, seven JavaScript checks, static build, exact production-row invariance, protected-layer nonmutation and bounded final diff. Temporary transaction machinery removed itself before commit. Permanent evidence is `data/live_intelligence/LIVE_CORRECTION_CONFLICT_CM_TRANSACTION_AUDIT_v0.1.md`.

### Stage 10G — post-CM pressure re-audit — DONE / CN SELECTED

Read-only coverage run `34441643238` confirms CM changed capability rather than population:

- Canonical remains 689 occurrences / 203 series;
- Monitor remains 26 adapters / 217 scoped occurrences / 48 series;
- Live remains 8 observations / 3 Canonical-linked;
- Analysis remains 22 reviews / 1 production Live input / 1 production revision;
- PIF remains one completed linked observation without an Analysis review;
- no unused completed same-anchor Analysis target exists;
- BARMM remains linked to a non-completed 14 September occurrence;
- Europe, Latin America and North America remain zero-Live prompts, not queues;
- Monitor and market-structure Analysis zeroes remain non-authorising prompts.

The qualitative pressure review compared current North American trade escalation and European oil-security context with a 9 September Brazilian fuel-policy intervention. It selects **CN — Brazil fuel-policy Live broadening** because the Brazilian development is independently important and exercises a novel unscheduled cross-domain combination: fiscal/tax policy + fuel/commodity shock + government-stated geopolitical context in Latin America. Regional diversification is a benefit, not a quota rule.

The selection remains conditional on a fresh post-CM-merge legal-status check. At review time, the Brazilian Finance Ministry announcement clearly supports an announced/adopted policy-development claim, but the complete final legal-instrument trail was not yet cleanly retrievable. CN must not silently upgrade announcement language to `in force`, invent legal numbering, manufacture exact source/event UTC timing or claim observed consumer-price/inflation effects.

Permanent selection evidence is `data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md`.

### Stage 10H — CN Brazil fuel-policy Live broadening — NEXT AFTER CM MERGE

CN is selected for **fresh post-merge design**, not pre-written population.

Minimum CN pressure:

1. start from exact then-current post-CM `main`;
2. freshly recheck Ministério da Fazenda, Presidency/Planalto and Diário Oficial sources for the 9 September fuel package, including corrections, legal numbers and effective status;
3. revise or abandon the candidate if the post-merge evidence materially changes the package;
4. if retained, keep the Live claim bounded to what competent first-party evidence supports — likely an unscheduled `POLICY_DEVELOPMENT` for Brazil rather than an invented Canonical occurrence;
5. preserve event time no finer than the supported civil date unless a competent source establishes a source-native clock;
6. do not promote the source page's displayed `18h47` to exact UTC without a competently established timezone;
7. distinguish the government's stated geopolitical/oil-shock rationale from WORLD SIGNALS causal attribution;
8. do not claim consumer prices fell, inflation changed, fuel supply improved or markets moved without separate evidence;
9. create no Monitor route or automation permission from public accessibility;
10. keep Analysis population and public projection closed;
11. preserve the CM correction/conflict contract and OPEC CE quarantine.

Canada–U.S. tariff escalation and EU oil-security context remain valid future Live candidates. They are deferred, not discarded, and should be reconsidered by later pressure rather than appended automatically.

'''

replace_between(
    ROADMAP,
    "### Stage 10F — CM Live correction / retraction / conflicting-report contract hardening — NEXT AFTER CL MERGE\n",
    "## Stage 11 — Calendar export / external write interfaces — LATER / WRITE GATE CLOSED\n",
    roadmap_replacement,
)

status_replacement = '''## Current pressure interpretation

CM is now materialised on the feature branch as a **no-production-population Live contract hardening tranche**. The mechanically derived block above is current: Live is v0.9 while production remains exactly 8 observations / 11 evidence / 3 Canonical-linked.

- **Canonical:** unchanged v0.42 / 689 occurrences. CM creates or mutates no Canonical identity, timing, lifecycle or provenance.
- **Sources / Change Ledger / Monitor:** unchanged v2.04 / 258 sources, v0.28 / 63 changes and v0.28 / 26 Monitor adapters. CM grants no automation permission and creates no route.
- **Live Intelligence:** v0.9 / 8 / 11 / 3 linked. `CORRECTED` / `RETRACTED` now require an explicit prior Live target, correction/revision evidence and strictly later observation time. `CONFLICTING_REPORTS` requires at least two unique evidence records from at least two distinct normalised providers plus a factual `conflict_description`. No winner or synthetic consensus is required. `conflict_description` is prohibited outside the conflict state.
- **Population:** all eight production observation objects and all eleven evidence objects are preserved exactly from merged CL. No current production row uses `CONFLICTING_REPORTS`, `CORRECTED` or `RETRACTED`.
- **External revisions:** `DATA_REVISION` remains distinct and may describe a newly observed revision to external data without inventing prior WORLD SIGNALS Live history.
- **Analysis:** unchanged 22 reviews / 97 evidence / 1 production Live input / 1 production revision. No automatic Live→Analysis relationship was created.
- **Waqa Moana:** remains historical motivating evidence only. CM does not reinterpret, resolve or populate it.
- **BARMM:** remains pre-election context for the planned 14 September 2026 occurrence; no outcome or post-event Analysis is manufactured early.
- **OPEC CE:** remains quarantined and excluded.

CM permanent transaction evidence is `data/live_intelligence/LIVE_CORRECTION_CONFLICT_CM_TRANSACTION_AUDIT_v0.1.md`. Guarded run `34441432538` / job `102757107224` passed on the first attempt, including **1,276 tests** with 68 historical-prestate skips, all governed validators, derived-state consistency, Python compilation, seven JavaScript checks, static build, exact production-row invariance, protected-layer nonmutation and bounded final diff. Temporary transaction machinery was removed before materialisation commit.

### Post-CM pressure — CN selected for fresh post-merge design

Read-only coverage run `34441643238` confirms the expected no-population result. Canonical remains 689 / 203 series, Monitor 26 adapters / 217 occurrences / 48 series, Live 8 / 3 linked, and Analysis 22 reviews / 1 Live input / 1 revision. Europe, Latin America and North America remain zero-Live prompts. PIF remains completed-linked without an Analysis review, but there is still no unused completed same-anchor Analysis target. Monitor category zeroes and the corporate/market Analysis zero remain prompts rather than queues.

Fresh qualitative comparison identifies a stronger next population candidate: Brazil's 9 September 2026 fuel-policy intervention. The Ministério da Fazenda states that the Federal Government adopted measures reducing federal PIS/Pasep and Cofins on gasoline and hydrated ethanol and authorising an adjustable road-diesel subsidy amid international oil-price volatility and supply restrictions that the government associates with geopolitical conflict.

`data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md` therefore selects **CN — Brazil fuel-policy Live broadening** for fresh design only after CM merges. The candidate is selected because it is independently important and exercises an unscheduled Latin American fiscal/commodity/geopolitical transmission signal, not because Latin America has a zero.

The selection is deliberately conditional. At the time of review, the Ministry announcement is clearer than the fully retrievable final legal-instrument trail. CN must freshly recheck Presidency/Planalto, Diário Oficial and Ministry sources after merge; must revise or abandon the candidate if evidence changes; and must not pre-write `in force`, exact legal numbering, exact UTC publication/event time, observed price/inflation effects, a Canonical occurrence, a Monitor route or an Analysis conclusion without separate support.

Current North American Canada–U.S. tariff escalation and European oil-security context remain credible future Live candidates but are deferred rather than appended mechanically. PIF Analysis and a market-structure review remain unjustified if their only purpose is to manufacture a bridge candidate or erase a histogram zero.

'''

replace_between(
    STATUS,
    "## Current pressure interpretation\n",
    "## Write and authority boundaries\n",
    status_replacement,
)

print("CM_CLOSEOUT_DOCS_UPDATED")
