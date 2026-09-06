# WORLD SIGNALS — post-AZ pressure audit BA v0.1

**Reference date:** 2026-09-06  
**Exact post-#81 main:** `802ca5b94b6e80a055ac363f48a6c8392f038048`

## Verified starting state

PR #81 / AZ is merged. Main preserves Canonical v0.38 / 688, Source Registry v1.80 / 243, Change Ledger v0.24 / 59, monitor expectations v0.10 / 8 adapters, Live Intelligence v0.4 / 4 reviewed internal observations / 6 evidence rows, and Analysis v0.17 / 21 reviews / 95 evidence rows with schema v0.6.

Production `live_inputs` is exactly 1, capped at 1 total and 1 per review. Public Live observation projection and public Live-input projection remain closed. Production `EXACT_TIMESTAMP_SERIES` remains 0. Automatic Canonical commit and Google Calendar writes remain closed.

AZ proved the first bounded relationship:

`completed Canonical occurrence -> reviewed Live factual observation -> reviewed Analysis input`

The next pressure must not be chosen merely because the Live population ceiling is now four or because a second bridge input is technically imaginable.

## Fresh current-development screen

A fresh 6 September screen confirms that viable Live material exists outside the already-exercised physical-shock, health-emergency and economic-data classes.

### Vietnam–Myanmar bilateral development

The Government of Viet Nam reported on 5 September that the two countries agreed to make defence and security cooperation a key pillar of bilateral ties, with additional cooperation across training, disaster response, transnational crime, investment and regional mechanisms.

Primary official source:
`https://en.baochinhphu.vn/viet-nam-myanmar-agree-to-transform-defense-security-cooperation-into-key-pillar-of-bilateral-ties-111260905161629675.htm`

This is a plausible future `GEOPOLITICAL_DEVELOPMENT` or `INSTITUTIONAL_DEVELOPMENT` specimen. It is not selected in BA because the more immediate architectural question is how later evidence changes an existing analytical judgement without rewriting history.

### OPEC+ 6 September meeting

OPEC's 2 August release explicitly scheduled the next meeting for 6 September 2026. At the time of the BA screening, current reporting described an expected October policy outcome but the authoritative 6 September outcome had not yet been established in the research record used for this audit.

Primary official schedule source:
`https://www.opec.org/pr-detail/1854611-2-august-2026.html`

WORLD SIGNALS must not promote an expected outcome into a confirmed Live fact merely because a meeting is due or because sources anticipate the decision.

### Other current candidates

Recent reporting also surfaces policy, institutional and geopolitical candidates in Latin America and Asia. These remain useful future pressure material, subject to first-order source verification. Their existence reinforces that BA is a sequencing choice, not a shortage-of-news choice.

## Competing pressures

### 1. Add a fifth Live observation

**Hold, not dismiss.**

A fifth observation could add a new class such as `POLICY_DEVELOPMENT`, `GEOPOLITICAL_DEVELOPMENT` or `INSTITUTIONAL_DEVELOPMENT`. That would broaden the Live sample, but it would not solve the downstream temporal-governance problem exposed by AZ: once later Live evidence becomes analytically relevant, how does WORLD SIGNALS change an Analysis without silently rewriting its prior state?

### 2. Add a second production Live -> Analysis input

**Reject for now.**

The system has only just opened one bounded production relationship. A second relationship would increase population before defining how a reviewed Analysis evolves over time. In particular, attaching later Live context to an existing review by editing that row in place would destroy the ability to answer what the analysis previously said and when it changed.

The absence of a completed/unreviewed Canonical frontier is also a useful counterweight: there is no clean new post-event packet demanding immediate bridge expansion.

### 3. Populate `EXACT_TIMESTAMP_SERIES`

**Hold.**

Market-data rights, canonical event time and event-specific market-reaction measurement remain separate constraints. The schema correctly treats zero exact series as acceptable. A rights-compatible exact-series specimen should be selected only when it creates genuine analytical value, not to remove a zero.

### 4. Broaden Monitor/source coverage

**Hold.**

Monitor concentration and source-governance gaps remain continuing pressures, but post-AZ does not reveal a new acute defect in the review-only monitor architecture. Route presence must not be expanded for geographic cosmetics.

### 5. Formalise Analysis revision lineage before further Live growth

**Selected.**

This is the first pressure created directly by successful Live -> Analysis integration.

The Charter requires versioned research infrastructure to preserve material revisions and, where practicable, answer:

> What did we previously believe, when did that change, and why?

It also requires uncertainty discipline and warns against post-hoc narratives that merely fit later observations to earlier events.

The current Analysis dataset has immutable `analysis_id` values and explicit `analysis_as_of_utc`, but no first-class distinction between:

- an original analytical snapshot;
- a later revision of that same analytical thread;
- a separate analytical perspective on the same Canonical occurrence;
- a factual correction;
- a reassessment caused by new Live evidence;
- a methodological or causal reassessment.

Without a revision contract, updating an existing review in place would make historical analytical state unauditable.

## BA architecture decision

BA should establish a **production-closed Analysis revision lineage grammar**. It should add zero production revisions and zero new Live observations.

A future revision will be a new Analysis row with a new immutable `analysis_id` and an explicit direct-parent field:

`revision_of_analysis_id`

The parent remains present. Supersession is derived from the child reference rather than written back into the parent.

### Required prospective revision fields

A populated revision must carry exactly the reviewed lineage metadata:

- `revision_of_analysis_id`
- `analysis_revision_kind`
- `analysis_revision_reason`

Permitted revision kinds should be controlled and initially cover:

- `FACTUAL_CORRECTION`
- `NEW_EVIDENCE`
- `NEW_LIVE_EVIDENCE`
- `METHODOLOGICAL_REASSESSMENT`
- `CAUSAL_REASSESSMENT`
- `SCOPE_OR_FRAMING_UPDATE`

### Lineage invariants

The prospective validator should require:

1. the parent Analysis row exists and is not the child itself;
2. the child preserves the same Canonical occurrence;
3. `analysis_as_of_utc` advances strictly beyond the parent snapshot;
4. cycles are prohibited;
5. branching from one parent is prohibited in the first controlled lineage mode so a single analytical thread cannot acquire ambiguous competing heads accidentally;
6. revision metadata cannot appear without a parent;
7. `NEW_LIVE_EVIDENCE` must introduce at least one explicit Live `observation_id` not already selected by the parent;
8. a Live observation never automatically creates or updates an Analysis revision;
9. Live revision/state-update semantics and Analysis revision semantics remain distinct;
10. automatic "latest Analysis" selection remains prohibited;
11. public collapse to a derived latest head remains prohibited until separately pressure-audited;
12. Canonical, Live, Monitor and Calendar state cannot be mutated through Analysis revision lineage.

## Public boundary

BA should not create a public "current analysis" view. With zero production revisions, the existing public Analysis projection remains semantically unchanged.

The prospective contract should strip revision-lineage metadata from public rows while the public revision-metadata gate is closed. A later pressure audit must decide whether the UI should show full revision history, derived heads, both, or neither. BA must not silently choose one.

## Transaction boundary

BA should mutate only:

- Analysis schema, advancing v0.6 -> v0.7;
- current project status;
- roadmap wording needed to record the new architecture.

It should add validator/module/tests/plan/audit infrastructure but must not mutate:

- Canonical Registry or schema;
- Source Registry;
- Change Ledger;
- biosecurity overlay;
- Monitor expectations or operations policy;
- Live Intelligence schema, observations or evidence;
- Analysis reviews or Analysis evidence.

The production revision count must remain exactly zero. Production Live-input count must remain exactly one. Production `EXACT_TIMESTAMP_SERIES` must remain zero.

## Decision

Proceed with BA as a production-closed Analysis revision-lineage foundation.

Do **not** add observation #5, do not add a second production Live input, do not revise the Japan FIES packet, do not collapse prior analytical snapshots into a synthetic latest state, and do not open any public or automatic write gate.

After BA, run another pressure audit before populating the first real Analysis revision or expanding Live/bridge population.
