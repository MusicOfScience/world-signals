# WORLD SIGNALS — post-BA pressure audit / BB selection v0.1

**Reference date:** 2026-09-06  
**Exact base:** `b8c5372198e3141c4c3f79ace13083877447f71b`  
**Selected tranche:** BB — BARMM parliamentary election source + Canonical coverage repair

## Post-BA checkpoint

BA is merged. The current governed checkpoint is:

- Canonical Registry v0.38 / 688 occurrences;
- Canonical schema v0.52;
- Source Registry v1.80 / 243 sources;
- Change Ledger v0.24 / 59 entries;
- biosecurity overlay v0.13 @ Canonical v0.38 / 688;
- monitor expectations v0.10 / 8 adapters;
- Live Intelligence v0.4 / 4 observations / 6 evidence rows;
- Analysis schema v0.7 / 21 reviews / 95 evidence rows;
- one production Live→Analysis input;
- zero production Analysis revisions;
- zero `EXACT_TIMESTAMP_SERIES` measurements.

## Pressure screen

### 1. First production Analysis revision

**Decision: HOLD.**

The existence of BA's revision grammar is not itself evidence that an existing review should change. No reviewed packet has acquired material later evidence that would justify revising its analytical conclusion during this audit. Creating a revision only to exercise the mechanism would pollute analytical history and violate the project's anti-post-hoc discipline.

### 2. Fifth Live observation

**Decision: HOLD for this tranche.**

A first-party Vietnam–Myanmar defence/security development is a valid candidate, but AW/AX already prove unscheduled, non-Canonical Live semantics. A fifth row would broaden the sample while adding less architectural information than the discovered upstream election gap.

### 3. Second production Live→Analysis relationship

**Decision: HOLD.**

AZ remains the only production relationship. There is no need to raise that cap merely to demonstrate repeatability; future expansion should be tied to a materially useful new interaction pattern.

### 4. Source / Canonical coverage omission — BARMM parliamentary election

**Decision: SELECT.**

The 14 September 2026 BARMM parliamentary election is absent from Canonical despite:

- authoritative COMELEC evidence for the polling date;
- official OPAPRU evidence that it is the first parliamentary election and a major Bangsamoro peace-process milestone;
- imminence inside the current forward horizon;
- material institutional/elections-governance significance;
- regional-balancing value in Southeast Asia / the Global South.

The omission is upstream of Live and Analysis. Repairing it first preserves the architecture rather than using downstream layers to compensate for Canonical incompleteness.

## Bias / taxonomy critique

This selection is not justified by a country quota or by a desire to add another election mechanically. It corrects a documented omission whose importance is easy to underweight in a Western/major-economy calendar:

- BARMM is a subnational autonomous regional polity, but the election is bound to a national peace agreement and institutional transition;
- political importance is high even though expected direct global market sensitivity is low;
- treating only national presidential/parliamentary contests as election anchors would create a structural bias against peace-process and autonomous-region institutional transitions.

Accordingly, BB separates:

- **intrinsic importance: HIGH**;
- **expected market sensitivity: LOW**;
- observed market response: not populated in advance.

## Source hierarchy and rights

COMELEC is the competent electoral authority and supplies the date. OPAPRU supplies peace-process context but is not required as a Canonical timing source.

No production crawling/reuse right is inferred from official status. The COMELEC source is registered with manual factual provenance only, automation held, and no candidate-level source content republished.

## Controlled target

BB may make only the following governed population changes:

1. Source Registry: add one COMELEC source;
2. Canonical Registry: add one BARMM polling-day `ELECTION_MILESTONE` occurrence;
3. Change Ledger: append one reviewed forward-occurrence admission record;
4. biosecurity overlay: advance version/checkpoint only, with semantic payload unchanged;
5. current status/roadmap: advance the recovery checkpoint and record the bounded repair.

No Canonical schema mutation is expected.

## Explicit non-targets

BB must not:

- add OPAPRU to the Source Registry merely because it informed significance screening;
- ingest certified candidate names or candidate-level data;
- invent polling hours, midnight timestamps or UTC precision;
- mark the future election completed;
- add election outcome facts before they exist;
- add a Live observation or Analysis review/revision;
- create a monitor adapter;
- enable automated Canonical commit;
- write Google Calendar.

## Exit gate

BB is mergeable only after a read-only simulation and controlled transaction prove:

- exact post-BA ancestry;
- one new source identity only;
- one new Canonical occurrence only;
- one new Change Ledger entry only;
- pre-existing Canonical/source/ledger rows byte-equivalent as Python data;
- overlay semantics unchanged except version/checkpoint;
- all Live and Analysis files unchanged;
- full validators/tests/build green;
- temporary workflows self-removed;
- one ordinary manual-merge PR.
