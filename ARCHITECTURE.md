# Executable architecture

## Why code starts now

The project has enough stable invariants to encode in software: stable identities, event/source separation, source-health quarantine, lifecycle/certainty vocabularies, review-only changes, timezone semantics and fail-closed monitor behaviour.

## Runtime layers

1. **Canonical Registry** — versioned JSON committed to the repository.
2. **Build / Projection** — validates canonical data and emits browser-safe derived JSON.
3. **Calendar / Web UX** — static HTML/CSS/JS served by GitHub Pages. Calendar, Event index and Monitor routes are projections only.
4. **Source / Change Monitor** — read-only Python adapters fetch and parse official sources, snapshot payload hashes, normalize evidence and compare against canonical occurrences or monitored legal inputs.
5. **Source Health** — transport/parser state is recorded independently of event state. Failure or absence cannot itself cancel, complete or reschedule an occurrence.
6. **Review Queue** — candidate JSON artefacts; human/review logic approves or rejects.
7. **Commit Tool** — future guarded transaction that applies approved changes after identity/provenance validation. Automatic use remains disabled.
8. **Live Intelligence / Analysis** — separate stores and views, not embedded into calendar timing fields.

## Current executable source-monitor contract

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

The scheduled GitHub monitor runs with `contents: read` permission. It hashes the canonical registry before and after each run and fails if those bytes change.

### Current live pilots

**RBA Financial Stability Review RSS/RDF**

The adapter executes against the official RBA XML feed. The real feed uses namespaced RDF/RSS rather than assuming a single RSS 2.0 shape, and regression tests cover both. Positive publication evidence may create a review candidate for the existing FSR occurrence; an empty, stale or failed feed cannot alter event state.

**Colombia SUIN / Socrata legal-instrument sentinel**

The adapter executes against the official Datos Abiertos Socrata API. Legal identity is typed: instrument type + number + year. This matters because number `111` and year `1996` identify more than one legal instrument in the inventory. The monitor therefore watches `DECRETO 111/1996` specifically. Inventory changes produce a legal-input review candidate and require clause-level SUIN verification before any derived budget rule can change.

## Static UX and runtime truth

GitHub Pages cannot honestly claim current monitor health merely because the last build was green. The web **Monitor routes** view therefore exposes configured routes, scope, cadence and permitted inference only. Runtime source health and review candidates remain timestamped GitHub Actions artefacts until a separate, provenance-safe status-publication mechanism is designed.

## GitHub is an execution shell, not the architecture

GitHub Actions runs validation and monitors, GitHub Pages hosts the read-only UI, and pull requests/commits provide review and audit history. The core Python, JSON contracts and static web output remain portable to another CI/host.

## Promotion path

```text
Research artifacts
  -> executable read-only registry + calendar UX       [DONE]
  -> fixture monitor + review candidates              [DONE]
  -> live source adapters, review-only                [ACTIVE: RBA + Colombia]
  -> scheduled source-health + candidate monitoring   [DONE for pilot routes]
  -> broader heterogeneous adapter population         [NEXT]
  -> reviewed commit transaction + rollback           [guarded next stage]
  -> optional calendar export                         [later]
  -> narrowly evaluated auto-commit classes           [only if evidence gate opens]
```

The remaining automatic-commit evidence gap is intentionally empirical: WORLD SIGNALS still needs a prospective reschedule observed across its own snapshots and an explicit cancellation of an already-canonical occurrence before that gate can even be reconsidered.
