# Executable architecture

## Governing rule

`WORLD_SIGNALS_PROJECT_CHARTER.md` is authoritative. The executable repository implements its layers as separate governed contracts rather than one blended event/news database.

Current post-#76 / AV foundation state:

- Canonical `v0.38 / 688`;
- Source Registry `v1.80 / 243`;
- Source/Change Monitor expectations `v0.10 / 8 adapters`;
- Live Intelligence `v0.1 / 0 observations / 0 evidence`, foundation gate closed;
- Analysis `v0.16 / 20 reviews / 91 evidence` on schema `v0.4`;
- automatic canonical commit OFF;
- Google Calendar writes OFF.

## Runtime layers

1. **Canonical Registry** — versioned authoritative event identities, lifecycle and timing.
2. **Calendar / Web projection** — derived read-only rendering; never the database.
3. **Source / Change Monitor** — read-only adapters inspect authoritative sources, source health and candidate changes.
4. **Live Intelligence** — factual current-development observations that may be scheduled or unscheduled and may optionally reference Canonical occurrences.
5. **Analysis** — reviewed interpretation of expectations, surprises, market observations, connections, noise, alternatives, second-order effects and falsifiers.

Supporting operational contracts include source governance, review-candidate state, reviewed Change Ledger, runtime evidence and noncanonical analytical/coverage overlays.

## Source / Change Monitor contract

```text
official endpoint
   |
   v
FETCH -> SNAPSHOT -> PARSE
   |          |
   |          +--> payload hash / source health
   v
normalized positive evidence
   |
   v
MATCH -> DIFF
   |
   +--> NO_CHANGE
   |
   +--> REVIEW CANDIDATE

Never:
source failure -> event cancellation
source absence -> event completion
parser success -> canonical write
```

The scheduled GitHub monitor runs with `contents: read` permission. It protects canonical bytes and cannot make direct canonical changes.

### Current configured adapter cohort

`data/monitor/expectations.json` v0.10 configures eight heterogeneous adapters:

1. **RBA Financial Stability Review RSS/RDF** — publication-completion sentinel.
2. **Colombia SUIN / Socrata Decree 111/1996** — typed legal-instrument sentinel with manual clause verification.
3. **EU Cyber Resilience Act Article 71 / Cellar** — legal-rule baseline and topology sentinel.
4. **EU CBAM verifier-report milestone** — legal milestone / Cellar topology sentinel.
5. **EU CBAM certificate-sale milestone** — amending-rule / parent-act topology sentinel.
6. **EU CBAM annual declaration / surrender deadline** — recurring legal-rule / topology sentinel.
7. **ONS release-calendar RSS** — publication schedule/date-change sentinel with official HTML verification requirement.
8. **EIA Weekly Petroleum Status Report schedule** — energy/publication-schedule sentinel.

Configuration does not mean every governed source is automation-cleared. Source rights, endpoint health, parser validation and route authority remain distinct gates.

## Live Intelligence foundation

AV introduces the first executable Live Intelligence contract at `data/live_intelligence/`.

```text
current development / observation
        |
        v
FACTUAL OBSERVATION
  - identity
  - verification state
  - domains / geography
  - evidence
  - optional canonical links
  - separate observation/event/publication time
  - explicit revision history
        |
        v
ANALYSIS may later interpret it
```

The AV v0.1 foundation is deliberately **zero-population**. Its validator rejects production observations and evidence until a later pressure-audited specimen explicitly opens the population gate.

Live Intelligence is not a synonym for the Source/Change Monitor. The monitor asks whether governed authoritative inputs changed; Live Intelligence records consequential factual developments in the world. A monitor parser failure is not a Live Intelligence fact.

Live Intelligence is also not Analysis. It may record a factual market observation, shock, announcement or revision, but it may not claim what was expected, what surprised, what caused a move or which interpretation is preferred.

Unscheduled physical shocks, health emergencies and geopolitical developments can therefore exist without inventing scheduled Canonical occurrences. If a Live observation references Canonical, the occurrence ID must resolve.

## Analysis contract

Analysis remains downstream interpretation. `data/analysis/schema.json` explicitly treats `LIVE_INTELLIGENCE` as upstream and preserves the Charter's separation between:

- what happened;
- what was expected;
- what surprised;
- what moved;
- what appears connected;
- what may be noise;
- alternatives;
- second-order effects;
- falsifiers.

Analysis evidence is not retrospectively migrated to Live Intelligence. Historical analytical packets remain frozen in their governed layer.

## Static UX and runtime truth

GitHub Pages cannot honestly claim current monitor health merely because a build was green. The Monitor view exposes configured routes, while runtime source health and review candidates remain timestamped evidence.

Likewise, AV emits `docs/data/live_intelligence.json` only as **foundation metadata**. It contains zero public observations and explicitly states that it is not a runtime feed. A browser Live Intelligence surface should not be introduced until a later population contract is proven.

## GitHub is an execution shell, not the architecture

GitHub Actions runs validation and monitors, GitHub Pages hosts read-only projections, and pull requests/commits provide review and audit history. The Python/JSON contracts remain portable to another CI/host. GitHub Actions artefacts are evidence surfaces, not canonical storage.

## Current promotion path

```text
Research / taxonomy / source governance                    [ONGOING]
  -> executable Canonical Registry + read-only UX           [DONE]
  -> review-candidate / source-health contracts              [DONE]
  -> heterogeneous live Source/Change adapters, review-only  [DONE: 8 configured]
  -> scheduled monitor execution / retained evidence         [DONE]
  -> controlled Analysis foundation + diverse sample         [DONE: 20 reviews / 18 event types]
  -> Live Intelligence executable zero-population foundation [AV]
  -> first pressure-audited Live Intelligence specimen       [NEXT AFTER AV MERGE]
  -> test prospective Live Intelligence -> Analysis linkage  [LATER, IF CONTRACT SURVIVES]
  -> broader Live Intelligence population                    [ONLY AFTER AUDIT]
  -> optional calendar export                                [LATER]
  -> narrow auto-commit classes                              [ONLY IF EMPIRICAL GATE OPENS]
```

A generic guarded reviewed commit/rollback mechanism remains an architectural objective; existing controlled tranche transactions demonstrate the safety pattern but do not open blanket automation authority.

The automatic-canonical-commit gate remains closed. Before it can even be reconsidered, WORLD SIGNALS still requires real prospective evidence including a reschedule detected against a prior canonical snapshot and an explicit cancellation of an already-canonical occurrence, under the governed review process.
