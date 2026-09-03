# Executable architecture

## Why code starts now

The project has enough stable invariants to encode in software: stable identities, event/source separation, source-health quarantine, lifecycle/certainty vocabularies, review-only changes, timezone semantics and fail-closed monitor behaviour.

## Runtime layers

1. **Canonical Registry** — versioned JSON committed to the repository.
2. **Build/Projection** — validates canonical data and emits browser-safe derived JSON.
3. **Web UX** — static HTML/CSS/JS served by GitHub Pages; searches and filters the projection.
4. **Source Monitor** — Python adapters fetch/parse official sources and emit assertions/diffs.
5. **Review Queue** — candidate JSON artifacts; humans approve or reject.
6. **Commit Tool** — future guarded transaction that applies approved changes after identity/provenance validation. Automatic use remains disabled.
7. **Live Intelligence / Analysis** — separate stores and views, not embedded into calendar timing fields.

## GitHub is an execution shell, not the architecture

GitHub Actions can run validation and monitors, GitHub Pages can host the read-only UI, and pull requests can provide review/audit history. The core Python, JSON contracts and static web output remain portable to another CI/host.

## Promotion path

```text
Research artifacts
  -> executable read-only registry + UX          [this repository]
  -> fixture monitor + review candidates         [this repository]
  -> live source adapters, review-only           [next]
  -> review/commit transaction + rollback        [next]
  -> optional calendar export                    [later]
  -> narrowly evaluated auto-commit classes      [only if evidence gate opens]
```
