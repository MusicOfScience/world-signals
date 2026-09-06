# WORLD SIGNALS — post-BB pressure audit BC

**Reference date:** 2026-09-06  
**Exact post-BB main base:** `c853f0ca40ff8974a070c31b70fb5fa5f0f01431`  
**Decision:** repair historical-checkpoint / descendant validation before any fifth Live observation, second production Live→Analysis relationship or first production Analysis revision.

## Pressure observed

BB itself was methodologically sound, but its ephemeral validation exposed a recurring architectural defect in older tranche helpers/tests: historical checkpoint values were sometimes being interpreted as permanent ceilings on legitimate descendants.

The failures were not evidence that later reviewed state was invalid. They came from stale assumptions such as:

- an Analysis schema introduced at v0.7 being required to remain exactly v0.7 forever;
- the AZ 21-review / 95-evidence checkpoint being treated as the only valid later Analysis population;
- the AV public projection test requiring the Canonical build checkpoint to remain v0.38 / 688 after Canonical had legitimately advanced;
- status helpers treating production gates and counts that were deliberately bounded for one tranche as immutable global state.

This creates two risks:

1. **false negatives:** a valid reviewed descendant is rejected because an old test encodes a historical ceiling;
2. **unsafe replay pressure:** maintainers may be tempted to weaken exact historical preconditions globally merely to make old helpers run on current state.

## Competing next steps considered

### 1. Fifth Live Intelligence observation

Rejected for BC. Live population is already explicitly gated pending another pressure audit. Adding a fifth row would test a new content class but would not repair the validation weakness BB just exposed.

### 2. Second production Live→Analysis relationship

Rejected for BC. AZ deliberately capped the inaugural relationship at one. Expanding before checkpoint semantics are clean would compound the same descendant-pressure problem.

### 3. First production Analysis revision

Rejected for BC. BA created the revision grammar precisely so the first real revision can be pressure-audited. Opening that gate while BA itself is still encoded in places as an exact current-state ceiling would be backwards.

### 4. BARMM downstream Live/Analysis population

Rejected for BC. BB created an upstream Canonical anchor. It did not pre-authorise downstream observations or analysis, and election day is still future. Population should follow evidence, not the existence of a new anchor.

### 5. Checkpoint / descendant contract repair

Selected.

## Contract decision

BC formalises one rule:

> **Freeze historical checkpoints; validate descendants only against invariants owned by the historical tranche.**

That means two different modes.

### Historical pre-materialisation mode

If a tranche target does not yet exist, its transaction helper must still require the exact reviewed prestate it was designed for. BC does **not** weaken historical transaction reproducibility or permit a tranche to be replayed opportunistically onto an unrelated later base.

### Reviewed descendant mode

Once the tranche target is already materialised, later reviewed state may legitimately grow. The old helper/test may validate:

- a minimum schema or dataset version;
- a minimum population required to preserve the historical specimen;
- stable IDs and relationships introduced by that tranche;
- structural invariants that were explicitly intended to survive later growth.

It must not automatically require:

- unrelated Source Registry or Change Ledger counts to remain frozen;
- monitor-adapter counts to remain frozen;
- later Analysis / Live populations to remain equal to the old checkpoint;
- a temporary production cap or closed gate to remain globally immutable after a separately reviewed future tranche changes it;
- a current recovery/status line to retain old counts merely to satisfy a historical helper.

## Scope of BC

BC is architecture-only. It adds no Canonical occurrence, no source, no Change Ledger admission, no Live observation, no Live evidence, no Analysis review, no Analysis evidence and no production revision.

BC introduces a small platform-independent checkpoint utility using dotted-numeric version comparison and explicit version floors, count floors, immutable values and required markers. It then migrates BA/AZ descendant handling onto that rule and adds regressions for future reviewed growth.

The AV foundation remains frozen in its own historical checkpoint metadata; its public projection continues to report the *current* Canonical build checkpoint rather than pretending v0.38 / 688 is still current.

## Invariants BC must preserve

- Canonical Registry remains v0.39 / 689.
- Source Registry remains v1.81 / 244.
- Change Ledger remains v0.25 / 60.
- Live Intelligence remains v0.4 / 4 observations / 6 evidence rows.
- Analysis remains schema v0.7 / 21 reviews / 95 evidence rows.
- production Live inputs remain 1.
- production Analysis revisions remain 0.
- production `EXACT_TIMESTAMP_SERIES` remains 0.
- automatic Canonical commit remains closed.
- Google Calendar writes remain closed.
- no public gate is opened by BC.

## Validation expectation

BC must prove both directions:

1. exact historical prestate requirements still fail closed before a tranche target exists; and
2. synthetic reviewed descendants with later versions/populations pass when the tranche-owned identity/relationship invariants remain intact.

A future pressure audit remains mandatory before the fifth Live observation, second production Live→Analysis link or first production Analysis revision.
