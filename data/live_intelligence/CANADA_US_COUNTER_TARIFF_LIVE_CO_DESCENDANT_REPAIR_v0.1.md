# WORLD SIGNALS — CO descendant repair v0.1

**Status:** REVIEWED DESCENDANT-SAFETY REPAIR / NO GOVERNED POPULATION WRITE  
**Reference date:** 2026-09-10  
**Exact post-CN base main:** `b2b9e85933dd1c5924af1228f47427d6b38bf967`  
**CO branch:** `feature/post-cn-canada-us-trade-live-co`

## Trigger

The first guarded CO transaction, workflow run `34466470104` / job `102836110628`, failed closed at the complete historical suite after CO simulation, focused CO tests, ephemeral materialisation, derived-state regeneration and all three governed validators had passed.

No governed CO materialisation was committed or pushed. Compilation, JavaScript checks, static build, protected-layer proof, bounded-diff cleanup and commit were skipped.

The complete suite ran **1,301 tests**, with **2 failures** and **68 historical-prestate skips**.

## Failure diagnosis

Both failures were in `tests/test_brazil_fuel_policy_live_cn.py` and were descendant-state coupling, not a CO payload or Live-validator defect.

### 1. Current evidence total mistaken for frozen CN checkpoint

`test_cn_checkpoint_records_zero_canonical_growth` correctly checked the frozen `cn_checkpoint` as 9 observations / 12 evidence rows / 3 Canonical-linked observations, but then incorrectly required the **current descendant evidence store** to remain exactly 12 rows.

A reviewed CO descendant legitimately adds two evidence rows while preserving the CN checkpoint and CN evidence row unchanged. The historical checkpoint must remain exact; the later repository total must not be treated as a ceiling.

### 2. Exact CN target validator used as a permanent descendant validator

`test_simulated_target_validates` called `validate_cn_contract(...)` unconditionally. That function is intentionally an exact CN transaction-target validator: it checks Live v0.10, 9 observations, 12 evidence rows and the CN population ceilings. On a legitimate CO v0.11 descendant it therefore reported expected target mismatches.

The validator itself is not weakened. Exact CN transaction semantics remain frozen. The test is repaired so that:

- when the repository is at exact CN v0.10, the exact `validate_cn_contract(...)` path still runs;
- on a reviewed later descendant, the test instead verifies the exact frozen `cn_checkpoint`, exact preservation of the CN observation and CN evidence object against the frozen CN payload, zero Canonical links on the CN observation, and validity of the **current** Live store through the main Live validator.

## Repair boundary

The repair changes only `tests/test_brazil_fuel_policy_live_cn.py`.

It does **not** change:

- CN research, plan, payload or transaction audit;
- `src/world_signals/brazil_fuel_policy_cn.py` or its exact target validator;
- any CN observation or evidence data;
- CO research, plan, payload or pure contract semantics;
- Canonical Registry, Source Registry, Change Ledger, Monitor, Analysis or Calendar state;
- CM correction/retraction/conflict semantics;
- OPEC quarantine lineage or tests.

## Required rerun

The CO guarded transaction must rerun from the branch containing this permanent test repair. Before any governed write it must exercise both:

- `tests.test_brazil_fuel_policy_live_cn`;
- `tests.test_canada_us_counter_tariff_live_co`.

The complete historical suite remains mandatory. A successful rerun may materialise CO only if all subsequent compile, JavaScript, static-build, protected-layer, existing-Live-row and bounded-diff gates also pass.
