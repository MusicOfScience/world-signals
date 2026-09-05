# WORLD SIGNALS — Priority-region Analysis S PR evidence v0.1

**Evidence date:** 2026-09-06  
**Base main:** `a7ba439673fa2c468f2c9c4ef28904fb25c688a7`  
**Reviewed transaction commit:** `d8c940b687b0f5dc0a94b606450a9568b43b5f2e`

## Purpose

Record the final validation evidence for Analysis population tranche S after the reviewed feature-branch transaction and before permanent pull-request CI.

S adds four reviewed post-event stress samples—one each for South Asia, Southeast Asia, Africa and Latin America—without changing canonical, source-governance, monitor, change-ledger or overlay state.

## Final analytical post-state

- canonical: v0.29 / 678 — unchanged
- Analysis schema: v0.2 — unchanged
- Analysis reviews: v0.2 / 2 → v0.3 / 6
- Analysis evidence: v0.2 / 5 → v0.3 / 14
- reviewed event-type diversity: 5
- eligible completed canonical anchors: 9
- reviewed canonical occurrences: 6
- broad readiness: `READY_FOR_CONTROLLED_EXPANSION`

`READY_FOR_CONTROLLED_EXPANSION` is a stress-test/readiness state only. It means the four priority geographic stress regions each have one audited sample and the minimum event-type-diversity gate is satisfied. It does not mean regional analytical completeness, representativeness or population authority.

## Four added samples

- South Asia — India Q1 FY2026-27 GDP: 7.8% y/y versus 7.1% cited expectation; `UPSIDE`. One next-session rupee observation is retained as a LOW-confidence `OBSERVED_ASSOCIATION`; the source identifies RBI intervention and dollar flows as stronger immediate drivers.
- Southeast Asia — Bank Indonesia 18–19 August decision process: 5.75% hold, expected by 27 of 28 Reuters-polled economists; `NO_CLEAR_SURPRISE`. No discrete market movement is promoted.
- Africa — CBE 20 August decision: rates unchanged, matching the admitted HC Securities expectation; `NO_CLEAR_SURPRISE`. The single institutional forecast is not relabelled as market consensus. No discrete market movement is promoted.
- Latin America — Argentina July CPI: 2.1% m/m versus 2.0% cited expectation; `UPSIDE` by 0.1 percentage point. No discrete market movement is promoted.

Three of the four new packets intentionally carry `what_moved: []`. A null market-reaction result is a legitimate analytical conclusion, not missing work.

## Full disposable post-state validation

GitHub Actions run `33975922999` / job `101332470890` — **SUCCESS**.

The disposable runner proved exact merged-main and upstream-file identity before applying S in-memory/on-runner only, then validated the proposed post-state.

Results:

- exact base/protected-state precondition: PASS
- fail-closed check-only transaction: PASS
- disposable apply: PASS
- exact Analysis-only mutation boundary: PASS
- canonical validator: **678 occurrences PASS**
- Analysis validator: **6 reviews / 14 evidence records PASS**
- full repository suite: **405 tests PASS, 15 skipped**
- Python compile: PASS
- browser JavaScript syntax checks: PASS
- static-site build: PASS
- built site: 678 events / 236 governed sources / 7 configured live-monitor routes / 6 analytical reviews
- readiness: `READY_FOR_CONTROLLED_EXPANSION`
- each of Africa, South Asia, Southeast Asia and Latin America: exactly 1 eligible / 1 reviewed / `REVIEWED_SAMPLE_PRESENT`

The first two disposable simulation attempts exposed only test-lineage/prose brittleness. The analytical transform and four proposed packets were not changed between the successful high-risk validation stages and the final green run. Repairs were narrowed to semantic descendant-safe assertions rather than terminal checkpoint numbers or wording fragments.

## Reviewed feature-branch apply

GitHub Actions run `33975968489` / job `101332593064` — **SUCCESS**.

The reviewed apply:

1. re-proved `origin/main` exactly `a7ba439673fa2c468f2c9c4ef28904fb25c688a7`;
2. proved canonical registry/schema, source registry, change ledger, biosecurity overlay, monitor expectations/operations policy and Analysis schema were still exact pre-state;
3. reran the fail-closed check-only transform;
4. applied S behind `WORLD_SIGNALS_APPLY_ANALYSIS_S=YES`;
5. validated canonical v0.29/678 and Analysis v0.3/6 + evidence v0.3/14;
6. ran focused S/Foundation/R tests successfully;
7. asserted the only generated data mutations were `event_reviews.json`, `evidence_registry.json` and the S transaction audit;
8. removed its own temporary workflow;
9. committed and pushed transaction commit `d8c940b687b0f5dc0a94b606450a9568b43b5f2e`.

The temporary workflow is absent from the reviewed branch head.

## Protected upstream boundary

No S changes are permitted to:

- `data/canonical/registry.json`
- `data/canonical/schema.json`
- `data/sources/registry.json`
- `data/changes/ledger.json`
- `data/coverage/biosecurity_overlay.json`
- `data/monitor/expectations.json`
- `data/monitor/operations_policy.json`
- `data/analysis/schema.json`

## Safety gates

- automatic canonical commit: **OFF**
- Google Calendar write: **OFF**
- canonical mutation from Analysis: **PROHIBITED**
- missing market baselines may not be reconstructed
- elapsed time never establishes canonical completion
- temporal sequence never establishes causality
- one audited sample per priority region never implies analytical completeness

Permanent pull-request CI must validate the durable final PR head independently of the disposable simulation/apply workflows.
