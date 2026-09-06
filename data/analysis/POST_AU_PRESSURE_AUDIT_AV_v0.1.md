# WORLD SIGNALS — post-AU pressure audit AV v0.1

**Exact post-#76 main:** `a487eaecd6c08e9692a42ce6ffed2dea1e455879`
**Reference date:** 2026-09-06

## Frozen checkpoint

- Canonical Registry: `v0.38 / 688`
- Canonical schema: `v0.52`
- Source Registry: `v1.80 / 243`
- Change Ledger: `v0.24 / 59`
- biosecurity overlay: `v0.13 @ canonical v0.38 / 688`
- monitor expectations: `v0.10 / 8 configured adapters`
- monitor operations policy: `v0.1`
- Analysis schema: `v0.4`
- Analysis reviews: `v0.16 / 20`
- Analysis evidence: `v0.16 / 91`
- reviewed event-type diversity: `18`
- Analysis-eligible completed occurrences: `21`
- production `EXACT_TIMESTAMP_SERIES`: `0`
- sole completed/unreviewed canonical occurrence: `WSO-MAC-B-0041`

AV is a pressure audit. A one-item frontier is not an instruction to consume the item.

## Decision

**Pause further Analysis population and build the executable Live Intelligence foundation with zero population.**

Do not add a twenty-first Analysis review merely to make the completed sample read `21/21`. Do not infer that an empty Live Intelligence store should immediately become a large news feed. Architecture comes before population.

## Why Japan remains held

`WSO-MAC-B-0041` — Japan Family Income and Expenditure Survey, July 2026 — remains a valid future Analysis specimen. It carries a useful data-vintage issue: the Statistics Bureau's 4 September 2026 publication notes retrospective revisions to April-June real-change history following the 2025-base CPI rebasing. That issue should be preserved if the occurrence is reviewed.

It does not currently outrank the architectural gap:

- `MACROECONOMIC_RELEASE` is already represented repeatedly in the reviewed sample;
- `DATA_RELEASE` surprise semantics are already exercised;
- a twenty-first review would add less new contract pressure than implementing a Charter-required layer that does not yet exist;
- queue exhaustion is not a project objective.

Japan is therefore **held, not rejected**.

## The missing layer is real

The Charter requires five distinct layers and explicitly defines Live Intelligence as the layer that monitors relevant news, policy announcements, economic data and market behaviour.

The repository currently has governed stores for:

- Canonical;
- Source/Change Monitor;
- Analysis;

but no `data/live_intelligence/` contract, dataset or validator.

This is not merely naming drift:

1. `data/analysis/schema.json` already lists `LIVE_INTELLIGENCE` as an upstream layer.
2. Earlier physical-risk and health/biosecurity audits explicitly route actual cyclones, outbreaks and operational emergencies to Live Intelligence / shock screening rather than the scheduled Canonical calendar.
3. Analysis now contains 20 reviewed specimens and 91 evidence rows, including newswire and market observations, but there is no reusable upstream observation contract through which current developments can exist before analytical synthesis.
4. Without a Live Intelligence contract, future unscheduled shocks risk being forced either into Canonical timing objects or directly into Analysis packets, blurring the architecture the Charter explicitly forbids blurring.

## What Live Intelligence is — and is not

Live Intelligence should hold **reviewed factual observations of current developments**, not causal interpretation.

It may eventually contain observations such as:

- official policy announcements;
- economic-data observations and revisions;
- market observations;
- geopolitical developments;
- physical shocks;
- health emergencies;
- institutional developments.

A Live Intelligence observation may link to zero, one or several canonical occurrences. An unscheduled shock does not need a fabricated canonical occurrence in order to exist.

Live Intelligence must not decide:

- what was expected;
- what surprised;
- what caused a market move;
- whether two adjacent developments are causally connected;
- what second-order effects follow;
- what interpretation is preferred.

Those remain Analysis questions.

## AV foundation contract

AV should create an executable `LIVE_INTELLIGENCE` layer at `v0.1` with **no populated observations and no populated evidence**.

The foundation should contain:

1. a machine-readable schema;
2. an empty observation store;
3. an empty Live-Intelligence evidence registry;
4. a validator and public metadata projection;
5. CI integration;
6. static-build integration that can expose only foundation metadata, not a fake live feed;
7. regression tests proving the layer boundaries;
8. documentation realignment where current operational documents materially misstate the repository state.

### Required layer boundaries

- Canonical mutation: prohibited.
- Calendar / Google Calendar write: prohibited.
- Source/Change Monitor mutation: prohibited.
- Analysis mutation: prohibited.
- Causal interpretation: prohibited.
- Market-move attribution: prohibited.
- Source failure or source absence: cannot create a Live Intelligence fact.
- Live evidence: cannot resolve or backfill missing canonical date/time.
- Unscheduled observations: may exist without canonical occurrence IDs.
- Canonical links: when present, must resolve to real canonical occurrence IDs.
- Observation time, source publication time and real-world event time: separate concepts.
- Revisions/corrections: must preserve prior observations rather than silently rewriting history.

## Foundation-only population gate

AV v0.1 should deliberately reject non-empty production observation/evidence population.

This is intentional. The first real specimen should be selected only after the architecture is merged and re-audited. That next specimen must stress the contract rather than merely provide convenient data.

A future population tranche should decide, using a real case, whether the minimal observation model needs additional identity, revision, rights or clustering semantics before opening broader population.

## Existing Analysis evidence is not migrated

The existing 91 Analysis evidence rows remain where they are.

AV must not retrospectively relabel historical reviewed evidence as Live Intelligence simply to make the new layer appear populated. The two evidence roles are different:

- Analysis evidence supports a reviewed analytical interpretation;
- future Live Intelligence evidence supports a factual observation before interpretation.

Any future cross-reference between Live Intelligence and Analysis must be introduced prospectively and validated explicitly.

## Documentation drift found by AV

Several operational documents have fallen behind the executable repository:

- `README.md` still reports Canonical `v0.20 / 669`, Source `v1.51 / 222`, monitor expectations `v0.6` and six routes;
- `PROJECT_STATUS.md` still opens on Canonical `v0.22 / 669`, Source `v1.63 / 225`, monitor expectations `v0.7` and six routes;
- `ARCHITECTURE.md` describes only RBA + Colombia as current live pilots and says broader heterogeneous adapter population is next;
- `ROADMAP.md` still describes live scheduled crawling and Analysis as future stages even though both are already implemented in controlled form.

These are documentation/recovery risks, not canonical-data errors. AV should update the compact operational docs and add a current override to the recovery checkpoint without deleting its historical audit trail.

## Explicit non-goals

AV does **not**:

- review `WSO-MAC-B-0041`;
- populate Live Intelligence observations;
- populate Live Intelligence evidence;
- ingest current news automatically;
- add market-data providers or infer reuse rights;
- migrate Analysis evidence;
- modify the Canonical Registry or schema;
- modify Source Registry or Source/Change Monitor configuration;
- modify Change Ledger;
- modify Analysis schema, reviews or evidence;
- create a browser surface claiming current live-intelligence status;
- enable automatic canonical commits;
- write Google Calendar;
- auto-merge.

## Post-AV question

After the foundation is merged, run a fresh pressure audit before population.

The next decision should be whether the first Live Intelligence specimen ought to stress:

- an unscheduled physical shock;
- a health emergency;
- a policy/geopolitical development;
- a data revision;
- or a market observation linked to an existing canonical occurrence.

The specimen should be chosen for contract pressure, international relevance and provenance quality — not convenience or headline prominence.
