# WORLD SIGNALS — Analysis sample audit Y method v0.1

**Reference date:** 2026-09-06  
**Exact base main:** `f05b9623f973aed84a420354d273e039a4b61f8e`

## Why audit now

The project working sequence calls for **sample population → audit → full population**. After X, the Analysis layer contains 11 reviewed completed-event specimens spanning 10 event types. That is sufficient to audit the sample's actual shape before adding more reviews merely because an eligible occurrence exists.

Y is therefore an audit checkpoint, not an Analysis-population tranche.

## What Y measures

Y derives its diagnostics from the live canonical registry, Analysis schema, reviewed-event dataset and analytical-evidence registry.

It reports:

- current Analysis eligibility/readiness;
- reviewed distribution by canonical region, category, event type, institution, intrinsic importance and expected market sensitivity;
- surprise-state and benchmark-type usage;
- interaction type, causal status, confidence and second-order status;
- presence/absence and type of market-response evidence;
- market-response measurement precision and whether values were independently reconstructed;
- evidence class, role and provider concentration for evidence actually referenced by reviewed packets;
- canonical regions/categories/event types that exist in the registry but have no completed Analysis-eligible anchor;
- completed-anchor dimensions that remain unreviewed;
- the marginal region/category/event-type/institution novelty of each currently eligible-unreviewed occurrence.

## What Y does not do

Y does **not**:

- treat regions, categories, event types, providers, surprise states or causal labels as population quotas;
- manufacture historical anchors to fill a gap;
- promote elapsed dates into completion evidence;
- require every controlled-vocabulary value to appear;
- reward stronger causal language;
- require a market movement for an important event;
- infer that a dominant evidence provider is unreliable merely because it is dominant;
- turn `READY_FOR_CONTROLLED_EXPANSION` into a claim that the sample is representative;
- treat exhaustion of the completed-but-unreviewed queue as a research objective.

## Audit logic

### 1. Readiness versus representativeness

The existing schema readiness state is retained exactly. Y separately measures whether the current **completed-anchor population** itself spans the regions/categories/event types already present elsewhere in the canonical registry.

A gap here is an upstream historical-anchor constraint. It is not an Analysis-layer permission to invent an event.

### 2. Marginal value of the eligible-unreviewed frontier

Each unreviewed completed occurrence is compared with the reviewed sample for whether it adds a new:

- region;
- category;
- event type;
- institution.

These are descriptive novelty dimensions, not an automatic ranking score. Importance, source quality and the contract pressure of the specimen still govern selection.

### 3. Market-response precision

Y distinguishes the existence of market-response rows from the precision used to establish them. In particular it counts `EXACT_TIMESTAMP_SERIES` separately from source-reported pre/post, source-reported change/endpoint, session-level and qualitative observations.

The aim is to detect whether adding another market-sensitive review would merely duplicate the existing measurement method or genuinely improve it.

### 4. Evidence concentration

Only evidence records actually referenced by reviewed packets enter the provider/class/role diagnostics. Provider concentration is reported as provenance shape, not as a quality score.

### 5. Anti-folklore / anti-balance rule

An absent `DOWNSIDE`, stronger causal status, `OBSERVED` second-order effect or particular market instrument is not a defect simply because the vocabulary contains that state.

Y must never recommend manufacturing an analytical state to make a chart look balanced.

## Mutation boundary

Y may create only its own audit report files and audit code/tests.

It must not mutate:

- `data/canonical/registry.json`;
- canonical schema;
- source registry;
- change ledger;
- biosecurity overlay;
- monitor configuration;
- Analysis schema;
- Analysis reviews;
- Analysis evidence;
- Calendar data.

## Decision use

The audit should answer two questions before the next population tranche:

1. Is the last current eligible-unreviewed occurrence genuinely the best next specimen, or merely the last item in a finite queue?
2. Does the larger marginal need sit upstream — for example a missing completed-anchor geography/domain — or in a different analytical contract such as higher-precision market measurement?

The output is a checkpoint for the next research decision. It is not itself authority to begin broad/full population.
