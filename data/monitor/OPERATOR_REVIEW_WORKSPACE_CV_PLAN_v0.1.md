# WORLD SIGNALS — operator review workspace CV plan v0.1

Date: 13 September 2026 (Australia/Melbourne)

## Governed base

- `main`: `a8c022ba6eb9e34962263538223f754aa62796c8`
- predecessor: merged PR #129, monitor health repair CU
- branch: `codex/operator-review-workspace-cv`

## Problem

The retained-review reducer already establishes stable proposition identity, recurrence aggregation, manual decision state and change-ledger reconciliation. The Operations view exposes those records but does not yet tell an operator which class of human work is next, distinguish repeated propositions at a glance, expose the immutable candidate evidence IDs, or support useful filtering and ordering.

## Bounded production change

- Advance `REVIEW_CANDIDATE_STATE_CONTRACT` from v0.1 to v0.2.
- Derive controlled routing metadata from existing review state only:
  - recurrence state;
  - operator attention class;
  - controlled next action.
- Make reconciliation, approved-transaction handoff, reobservation after a decision, repeated pending review and first pending review visibly distinct.
- Add search, state filtering, attention filtering and deterministic attention/latest/recurrence ordering.
- Show candidate evidence-object IDs already permitted by the public contract.

## Safety boundary

- Operator attention is workflow routing, not event importance, risk severity, probability or market impact.
- A next-action label is not an executable action and grants no browser write authority.
- Approval remains a reviewed repository decision; Canonical mutation requires a separate guarded transaction and change-ledger link.
- No raw old/new values, source assertions, snapshots, parser errors, rule state or topology enters the public projection.
- No Canonical, Sources, Change Ledger, Monitor expectations, Live Intelligence, Analysis or Calendar population mutation.
- OPEC quarantine and `HANDOFF_PROTOCOL.md` remain unchanged.

## Gate

- reducer state/precedence and public-field tests;
- browser read-only and responsive UX tests;
- full ordinary validation suite at exact committed head;
- exact-head governed local operations run using real retained local history;
- browser QA of search/filter/sort on the generated projection;
- structural diff, protected-path and residue checks;
- hosted CI when runnable, otherwise the owner-authorised local exact-head fallback.
