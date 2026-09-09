# WORLD SIGNALS — post-CH pressure audit CI v0.1

**Reference date:** 2026-09-10  
**Exact merged CH base:** `c4f359c2c70f023c32990f20234aaf154dced152`  
**Selected tranche:** bounded NOAA/NHC Atlantic-season Monitor activation

## 1. Current governed pressure

CH left governed population unchanged while making recovery truth mechanically derivable:

- Canonical Registry `v0.41 / 689`;
- Source Registry `v2.02 / 257`;
- Monitor expectations `v0.27 / 25` with 24 unique configured sources and 215 explicitly scoped Canonical occurrences;
- Live Intelligence `v0.7 / 7 observations / 10 evidence`, including two Canonical-linked observations;
- Analysis `22 reviews / 97 evidence`, with one production Live input and one production revision.

Counts are diagnostics, not quotas.

## 2. Candidate comparison

### Second Live → Analysis input — hold

The new CG BARMM `CONTEXT_FOR` observation points to the 14 September 2026 BARMM election, which is still pre-event at this boundary. The current production Analysis contract requires a reviewed post-event packet anchored to a `COMPLETED` Canonical occurrence. Forcing the relationship now would collapse Live context into Analysis before the event.

### Another Live specimen — lower information value

The controlled Live population already exercises unscheduled physical shock, evolving health state, scheduled economic outcome, unscheduled geopolitical development, institutional development and `CONTEXT_FOR` pre-event context. Adding another row without a new contract would mostly increase count.

### Second Analysis revision — no demonstrated revision pressure

No newly reviewed evidence at the CH boundary requires another production revision merely to exercise lineage again.

### NHC Atlantic-season Monitor — selected, narrowly

CF already validated a fail-closed adapter for exactly two existing Atlantic hurricane-season occurrences. Activation now exercises a genuinely missing scheduled Monitor domain: `PHYSICAL_CLIMATE_RISK`.

This is **not a storm tracker**. The route monitors the authoritative NHC season-definition semantics for the existing physical-risk windows. NHC RSS is source-health corroboration only and carries no season-date, lifecycle, certainty, storm-impact or Canonical-write authority.

The architecture value is therefore a heterogeneous physical-risk-window sentinel, not cosmetic category filling.

## 3. Fresh authoritative review

On 2026-09-10 the NOAA National Hurricane Center climatology page continued to define the Atlantic hurricane season as **June 1 through November 30**. NHC's official RSS directory continued to advertise Atlantic tropical-weather feeds. The National Weather Service disclaimer continued to describe NWS web information as public-domain unless otherwise noted and its appropriate-use guidance continued to ask automated users to request only necessary data at sensible cycles.

CI therefore permits a bounded low-rate route only. Public-domain status is not treated as blanket permission for unrelated NOAA/NHC polling.

A live GitHub Actions preflight must still re-check the exact NHC climatology, RSS and robots surfaces before the controlled transaction may materialise.

## 4. Activation boundary

CI may change only:

- the existing `WSSRC-RISK-002` source-governance fields necessary to describe bounded unattended retrieval;
- `data/monitor/expectations.json` by appending one exact two-occurrence route;
- `scripts/run_live_monitor.py` to execute that configured route;
- derived noncanonical recovery surfaces after the governed change;
- CI-owned audit/plan/test/helper files.

CI may not change Canonical occurrences, Canonical schema, Change Ledger, Monitor operations policy, Live Intelligence population, Analysis population, biosecurity overlay, Google Calendar state or any external calendar.

## 5. Exact route semantics

Target source: `WSSRC-RISK-002` — NOAA National Hurricane Center.

Target series: `WSER-RISK-ATL-HURR`.

Exact occurrence allow-list:

- `WSO-COM-A-0049` — Atlantic hurricane season 2026;
- `WSO-COM-A-0050` — Atlantic hurricane season 2027.

Authoritative semantic surface: NHC tropical-cyclone climatology.

Current baseline: `06-01` → `11-30`.

Operational corroboration: NHC Atlantic Tropical Weather Outlook RSS health only.

The daily WORLD SIGNALS Monitor scheduler means the activated route is honestly recorded as daily. Its request budget is bounded to one climatology request plus one RSS-health request per run. CI does not pretend that a route-level cadence string independently throttles the shared workflow.

## 6. Authority gates

All remain false:

- schedule authority;
- lifecycle authority;
- certainty authority;
- automatic new-occurrence creation;
- automatic Canonical commit;
- Google Calendar write;
- automatic Live or Analysis promotion.

A semantic boundary mismatch may create a review candidate only. RSS absence, no active storms, feed failure or storm activity has no event-state meaning.

## 7. OPEC quarantine

CE/OPEC remains explicitly excluded. CI does not reopen, merge, cherry-pick, rebase, materialise or use PR #113 / `feature/post-cd-pressure-audit-ce` as a base. `OPEC_QUARANTINE.md` and its regression remain protected.

## 8. Merge gate

The transaction is eligible for PR handoff only after a fresh live NHC preflight, exact-base assertions, controlled materialisation, Canonical/Live/Analysis validators, derived-state check, NHC and OPEC regressions, full test suite, Python/JavaScript checks, static build, protected-layer hash audit, bounded diff audit, temporary workflow removal and ordinary PR CI success.
