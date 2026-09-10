#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_section(path: str, start: str, end: str, replacement: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if text.count(start) != 1 or text.count(end) != 1:
        raise SystemExit(f"{path}: section markers not unique")
    a = text.index(start)
    b = text.index(end, a)
    target.write_text(text[:a] + replacement.rstrip() + "\n\n" + text[b:], encoding="utf-8")
    print(f"updated {path}")


def insert_before_once(path: str, marker: str, block: str, sentinel: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if sentinel in text:
        print(f"{path}: insertion already present")
        return
    if text.count(marker) != 1:
        raise SystemExit(f"{path}: insertion marker not unique")
    target.write_text(text.replace(marker, block.rstrip() + "\n\n" + marker, 1), encoding="utf-8")
    print(f"inserted into {path}")


def main() -> int:
    insert_before_once(
        "PROJECT_STATUS.md",
        "## Current pressure interpretation",
        """### PR #119 — CK: PIF lifecycle/provenance completion repair — MERGED

CK corrected CJ's apparent PIF absence finding after an identity-aware probe found the existing stable `WSO-INT-A-0001` / `WSER-INT-PIF-LEADERS` family. It preserved the event's Palau civil-date timing, host binding and sensitivity metadata, moved lifecycle from `ACTIVE` to first-party-evidence-backed `COMPLETED`, added one supporting-only Cook Islands completion source, and repaired descendant-unsafe historical Canonical/Source/Ledger assertions. No PIF Monitor, Live or Analysis row was created in CK.
""",
        "### PR #119 — CK: PIF lifecycle/provenance completion repair — MERGED",
    )

    replace_section(
        "PROJECT_STATUS.md",
        "## Current pressure interpretation",
        "## Write and authority boundaries",
        """## Current pressure interpretation

CL is now materialised on the feature branch as one bounded scheduled institutional-outcome Live specimen. Population counts remain diagnostic rather than selection rules.

- **Canonical:** unchanged v0.42 / 689. The completed PIF anchor `WSO-INT-A-0001` remains byte-semantically unchanged by CL: 30 August–4 September 2026, `Pacific/Palau`, DAY precision, confirmed lifecycle completion from CK.
- **Sources / Change Ledger / Monitor:** unchanged v2.04 / 258 sources, v0.28 / 63 changes and v0.28 / 26 Monitor adapters. CL creates no PIF Monitor route and acquires no automation permission from the Cook Islands evidence page.
- **Live Intelligence:** v0.8 / 8 observations / 11 evidence / 3 Canonical-linked. CL adds exactly one `PRIMARY_CONFIRMED` `INSTITUTIONAL_DEVELOPMENT`, `WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001`, linked `OUTCOME_OF` the completed PIF anchor. Its factual scope is the Leaders' Retreat resolution of a Pacific-led framework for engagement with partners. It does not represent the whole Forum Communiqué and contains no Analysis fields.
- **Fresh evidence correction:** CL excluded Waqa Moana after finding unreconciled institutional-status wording: the Australian PM release used `unanimously endorsed`, while indexed final-communiqué text used `agreed in principle` and noted further national consultations. The final Forum Secretariat PDF was not directly retrievable through the controlled automated path, so CL did not choose a stronger formulation or invent a reconciliation.
- **Analysis:** unchanged 22 reviews / 1 production Live input / 1 production revision. The post-CL frontier now contains one completed linked Live observation without an Analysis review — PIF — but still **zero bridge-ready completed same-anchor candidates**. PIF is not automatically promoted into Analysis.
- **BARMM:** remains linked pre-election context for the `PLANNED` 14 September 2026 occurrence; no post-event outcome or Analysis is manufactured before authoritative completion evidence.
- **OPEC CE:** remains quarantined and excluded.

CL's permanent transaction evidence is `data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_TRANSACTION_AUDIT_v0.1.md`. Successful guarded run `34436154025` passed exact-base gating, focused CL tests, all governed validators, derived-state consistency, **1,262 tests** with 68 historical-prestate skips, Python compilation, seven JavaScript checks, static build and bounded/protected-layer gates. Temporary write-capable scaffolding was removed after materialisation.

### Post-CL pressure — CM selected for fresh post-merge design

Read-only coverage run `34436436416` confirms Live is now 8 / 3 linked and removes Oceania / Pacific from the zero-Live prompt set. Europe, Latin America and North America remain prompts only. `CLIMATE_ENVIRONMENT` and `HEALTH_BIOSECURITY` still have no configured Monitor scope, and `CORPORATE_FINANCIAL_MARKET_STRUCTURE` still has no Analysis review; none is a queue.

The stronger current pressure is a capability weakness exposed by CL's source disagreement. Live already names `CONFLICTING_REPORTS`, `CORRECTED` and `RETRACTED`, but the executable contract is not mature enough for broader population: correction/retraction does not yet require correction-role evidence or later chronology, and conflicting-report state does not yet require distinct providers plus an explicit factual disagreement description.

`data/coverage/POST_CL_PRESSURE_AUDIT_CM_v0.1.md` therefore selects **CM — Live correction / retraction / conflicting-report contract hardening** for fresh design only after CL is merged. CM should be a no-production-population foundation: strengthen schema/validator invariants and prove them with synthetic fixtures, while preserving all eight Live rows and eleven evidence rows. It must not reinterpret Waqa, create a synthetic conflict specimen, open public projection, create another Live→Analysis link, or mutate Canonical/Monitor/Analysis state.

The post-CL audit also explicitly rejects two tempting shortcuts: creating a PIF Analysis review merely to manufacture a bridge target, and backfilling a mechanical market-structure event merely to erase the last Analysis category zero.
""",
    )

    replace_section(
        "ROADMAP.md",
        "### Stage 10D — CL bounded PIF scheduled institutional-outcome Live specimen",
        "## Stage 11 — Calendar export / external write interfaces",
        """### Stage 10D — CL bounded PIF scheduled institutional-outcome Live specimen — DONE / GUARDED

CL starts from exact post-#119 main `aef4642863438e2170ae9a49160b7368c850b819` and materialises one bounded `PRIMARY_CONFIRMED` `INSTITUTIONAL_DEVELOPMENT`:

- `WSLI-INST-PIF-PARTNER-FRAMEWORK-20260904-001`;
- region `Oceania / Pacific`;
- domain tags `INSTITUTIONS` + `GEOPOLITICS`;
- `OUTCOME_OF` → completed `WSO-INT-A-0001`;
- one primary-official Cook Islands PMO evidence row;
- no manufactured `event_time`;
- no market, surprise, causal or second-order claim.

Live advances from v0.7 / 7 observations / 10 evidence / 2 Canonical-linked to **v0.8 / 8 / 11 / 3**. Canonical, Sources, Change Ledger, Monitor and Analysis remain unchanged.

Fresh preflight narrowed the proposed payload. The Australian Prime Minister's Waqa Moana release used `unanimously endorsed`, while indexed final-communiqué text used `agreed in principle` and noted further national consultations. Because the authoritative Forum Secretariat PDF was not directly retrievable through the controlled automated path, CL excludes Waqa rather than silently choosing the stronger wording. The discrepancy is preserved as evidence pressure, not resolved by assertion.

The guarded transaction also repaired descendant-unsafe CG/CJ/BF/BD tests that had frozen historical Live v0.7 current-state values or population labels as permanent ceilings. Their historical specimen semantics and safety gates remain tested. Successful run `34436154025` passed the complete **1,262-test** suite plus validators, compilation, seven JavaScript checks, static build and bounded/protected-layer gates. Permanent transaction evidence is `data/live_intelligence/PIF_PARTNER_FRAMEWORK_LIVE_CL_TRANSACTION_AUDIT_v0.1.md`.

Automatic ingestion, Canonical commit, Calendar write, PIF Monitor creation, Live→Analysis promotion and public Live projection remain closed.

### Stage 10E — post-CL pressure re-audit — DONE / CM SELECTED

Read-only coverage run `34436436416` reports:

- Canonical 689 occurrences / 203 series;
- Monitor 26 adapters / 217 scoped occurrences / 48 series;
- Live 8 observations / 3 Canonical-linked;
- Analysis 22 reviews / 1 production Live input / 1 production revision;
- completed linked Live observations with an existing unused Analysis target: **0**;
- completed linked Live observations without an Analysis review: **1** — the new PIF outcome;
- linked non-completed observations: **1** — BARMM pre-election context;
- Europe, Latin America and North America remain zero-Live prompts;
- Monitor category zeroes and the corporate/market Analysis zero remain non-authorising prompts.

PIF is not bridge-ready. No same-anchor Analysis review exists, and the current bridge policy remains `CONTROLLED_SINGLE_PRODUCTION_LINK` with its one production slot already occupied by Japan FIES. Creating an Analysis review merely to manufacture a bridge target is prohibited by the evidence-first architecture.

The stronger pressure is correction/conflict handling. CL's Waqa source disagreement demonstrates why named verification states are insufficient without executable semantics. The permanent pressure decision is `data/coverage/POST_CL_PRESSURE_AUDIT_CM_v0.1.md`.

### Stage 10F — CM Live correction / retraction / conflicting-report contract hardening — NEXT AFTER CL MERGE

CM is selected for **fresh post-merge design** and should add no production observation merely to exercise the contract.

Minimum CM pressure:

1. start from exact then-current post-CL `main`;
2. preserve all eight current Live observations and eleven evidence rows unless an explicitly reviewed schema migration requires otherwise;
3. keep state updates distinct from corrections/retractions and preserve external `DATA_REVISION` semantics;
4. require `CORRECTED` / `RETRACTED` observations to reference the prior observation and at least one evidence row carrying `CORRECTION_OR_REVISION`;
5. require correction/retraction observation time to be later than its revision target;
6. retain self-reference and revision-cycle prohibitions;
7. design a bounded `CONFLICTING_REPORTS` contract requiring multiple evidence records from distinct providers plus an explicit factual description of the disagreement;
8. never require a conflicting-report state to choose a winner or manufacture consensus;
9. prove valid/invalid shapes with synthetic fixtures rather than creating a production conflict/retraction row for coverage;
10. treat Waqa as motivating historical evidence only; do not reinterpret or populate it automatically;
11. keep Canonical, Sources, Change Ledger, Monitor, Analysis, Calendar/public projection and OPEC quarantine unchanged;
12. keep automatic ingestion, automatic Canonical commit, automatic Monitor→Live and automatic Live→Analysis closed.

The precise field shape for conflict description remains a CM design question, not a pre-authorised schema decision.

### Stage 10G — further broadening / deepening — AFTER CM AUDIT

After CM, rerun pressure rather than treating Europe, Latin America, North America, corporate/market Analysis or PIF bridge potential as a FIFO queue. Candidate classes remain evidence-driven Live expansion, rights-cleared Monitor expansion, identity-aware Canonical/source repair, independently justified Analysis, valid same-anchor Live→Analysis, or evidence-driven Analysis revision.

BARMM remains pre-event until the 14 September 2026 election occurs and is authoritatively established as completed. Do not pre-write its post-event Analysis or infer an outcome from pre-election context.

Broader population must continue to establish geographic/domain balance, noise controls, retention and provenance; CM specifically addresses correction/retraction/conflict handling before any high-volume Live ingest is considered. Platform independence remains mandatory.
""",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
