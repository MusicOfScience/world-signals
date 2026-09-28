# Step 14A climate World State candidate

Status: `REVIEW_PENDING` / `READY_FOR_HUMAN_COMPONENT_REVIEW`

This is retained non-governed audit evidence. It is not a production World
State component, snapshot, admission transaction or public projection.

## Review scope

The package contains exactly two independently reviewable candidates derived
from the governed Analysis review `WSAN-AU-TCSEASON-2025-26-001`:

1. `BASELINE` — `WSBASE-CLIMATE-AU-TC-CLIMATOLOGY-1980-81-001-R1`
2. `DIMENSION_ASSESSMENT` — `WSDIM-CLIMATE-AU-TCSEASON-2025-26-001-R1`

The baseline represents the Australian Bureau of Meteorology's official
climatological reference of about 10 Australian-region tropical cyclones per
season since 1980–81. The source-native period is retained without invented
UTC bounds. This is not a 2025–26 Forecast, probability distribution, severe-
count benchmark, damage baseline or abnormality threshold.

The dimension candidate represents the completed 2025–26 Australian-region
tropical-cyclone physical-risk window. It retains realised measurements of 11
cyclones, 7 severe systems, 2 Category 5 systems, 4 cyclone-strength mainland
landfalls and 2 tropical-low mainland crossings. Direction is
`NOT_ASSESSED`; persistence is a completed historical window; and
`what_surprised` remains `NOT_ESTABLISHED`.

## Deliberate non-claims

The candidate does not infer forecast surprise, abnormality, damage, exposure,
loss, mortality, GDP, supply-chain impact or climate attribution. Warm SST and
broader climate material remain `COMMON_DRIVER_CONTEXT` with
`NOT_A_CAUSAL_CLAIM`. The aggregate season is not a named-cyclone shock.

No anomaly, Negative Evidence, Relationship, Risk/Regime, Scenario, Forecast,
Outcome, Actor assertion, implementation claim, competing hypothesis or model
disagreement is created. No freshness policy or present-tense cyclone-risk
claim is invented for the completed historical window.

## Lineage and fingerprints

- Analysis: `WSAN-AU-TCSEASON-2025-26-001`
- Canonical occurrence: `WSO-RISK-AU-TC-2025-26`
- Knowledge boundary: `2026-09-05T23:35:00Z`, the governed Analysis review time
- Candidate construction cutoff: `2026-09-28T13:30:00Z`
- Source manifest fingerprint: `672924298cedc998f243531e27e6bdb577220f357169c2959ecf26d74c02d8a7`
- Baseline candidate fingerprint: `17b586da3a8733ab1aad5051fd35e35d9b016167450b937d16292fa49cc2991c`
- Dimension candidate fingerprint: `20dc4e2177aa5ea9284cdc962a78fe05cd8a39f71ae41b0547c34bbd35b3c9e9`
- Package semantic fingerprint: `fe6a9f080037c753de5b64507789b1a70238201005ad5960a069d9aaf6a35687`

The four Bureau evidence rows are retained as one institutional source family;
separate rows are not treated as independent corroboration. Model runtime
identity/version/reasoning metadata is unavailable and remains explicitly
`UNAVAILABLE`; model output is not factual corroboration.

## Human review questions

For each candidate, the reviewer must explicitly choose `ACCEPT`, `DEFER` or
`REJECT`:

- Is Bureau climatological planning guidance appropriately represented as a
  governed `OFFICIAL_REFERENCE` Baseline with source-native precision?
- Does the Dimension Assessment accurately represent the completed seasonal
  physical-risk state without promoting hazard counts into forecast surprise,
  impact or attribution?

The candidates remain `UNDER_REVIEW`, `UNRESOLVED`, `INTERNAL_ONLY`, and have
`write_targets: []`. Production state remains unchanged.
