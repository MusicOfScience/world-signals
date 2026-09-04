# WORLD SIGNALS — Biosecurity Taxonomy Diagnostic v0.1

**Reference date:** 2026-09-04  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Purpose:** preserve the evidence recovered from the temporary read-only biosecurity taxonomy diagnostic before that workflow is removed.

## Diagnostic method

A read-only GitHub Actions workflow inspected the canonical registry without mutating any project data. It:

1. selected all records whose primary category is `HEALTH_BIOSECURITY`;
2. grouped those records by stable `series_id`;
3. recorded institution, subcategory, event type and selected health-governance fields; and
4. searched the complete canonical registry for adjacent institutional terms covering WOAH, IPPC/CPM, BWC/UNODA, Africa CDC and One Health.

Workflow run: `33817225156` / job `100851933825` — **SUCCESS**.

## Exact canonical finding

`HEALTH_BIOSECURITY` contains **10 occurrences across five series**. Every series is a World Health Organization series:

| Series | Institution | Subcategory | Event type | Occurrences | Health process |
| --- | --- | --- | --- | ---: | --- |
| `WSER-HEALTH-WHA` | World Health Organization | `global_health_governance` | `HEALTH_GOVERNANCE_EVENT` | 1 | `GLOBAL_HEALTH_GOVERNANCE` |
| `WSER-HEALTH-WHO-EB` | World Health Organization | `global_health_governance` | `HEALTH_GOVERNANCE_EVENT` | 1 | `GLOBAL_HEALTH_GOVERNANCE` |
| `WSER-HEALTH-WHO-IGWG` | World Health Organization | `pandemic_governance` | `HEALTH_GOVERNANCE_EVENT` | 1 | `PANDEMIC_TREATY_NEGOTIATION` |
| `WSER-HEALTH-WHO-PBAC` | World Health Organization | `health_budget_governance` | `HEALTH_GOVERNANCE_EVENT` | 2 | `HEALTH_BUDGET_GOVERNANCE` |
| `WSER-HEALTH-WHO-RC` | World Health Organization | `regional_health_governance` | `HEALTH_GOVERNANCE_EVENT` | 5 | `REGIONAL_HEALTH_GOVERNANCE` |

The WHO IGWG series carries the Pathogen Access and Benefit Sharing (PABS) Annex as its pandemic-agreement component. The WHA, WHO Executive Board and IGWG series are marked high health-security relevance; the PBAC series is medium and regional committees medium-high. All route outbreaks away from scheduled governance into the shock-candidate path.

## Adjacent-institution search

The diagnostic searched canonical name, institution, notes and subcategory fields for:

- World Organisation for Animal Health / WOAH;
- International Plant Protection Convention;
- Commission on Phytosanitary Measures;
- Biological Weapons Convention;
- UNODA;
- Africa CDC; and
- One Health.

**Result: zero canonical adjacent matches.**

This means the present institutional concentration is not merely a category-count artefact hiding already-canonical WOAH/IPPC/BWC/Africa CDC material. The canonical health/biosecurity footprint is genuinely WHO-only at this checkpoint.

## Architectural implication

Do **not** repair this concentration by moving unlike institutions into `HEALTH_BIOSECURITY` or by creating placeholder canonical series.

The next architecture should treat broader biosecurity as a **non-exclusive derived analytical/coverage overlay** keyed to stable canonical identities while preserving each event's natural primary category. Candidate system families include:

- human-health governance;
- animal / zoonotic health;
- plant / phytosanitary security;
- biological-security / arms-control governance; and
- One Health as a cross-cutting relationship rather than a forced primary category.

At v0.1, only canonical series that actually exist should be mapped. WOAH, IPPC/CPM, BWC/UNODA and Africa CDC remain research/candidate nodes until separately admitted through normal source, timing and canonical-review gates.

## Safety boundary

This diagnostic made **zero canonical changes**, **zero source-registry changes**, **zero monitor changes** and **zero Calendar writes**. It does not authorize event population.
