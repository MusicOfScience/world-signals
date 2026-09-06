# WORLD SIGNALS — post-AV pressure audit AW v0.1

**Exact post-#77 main:** `4768c73532c4ba4038b30314079b85be64fbee01`
**Reference date:** 2026-09-06

## Decision

Open Live Intelligence only far enough to admit **one controlled physical-shock specimen**: the 26 August 2026 Bhote Koshi / Rasuwa flash flood in Nepal.

Do not open a general news feed. Do not create story clustering. Do not project observations publicly. Do not consume the held Japan Analysis specimen merely because it remains unreviewed.

## Candidate comparison

AW compared five specimen classes.

### 1. Nepal flash floods — selected

Primary official evidence is unusually contract-rich.

The Government of Nepal Ministry of Home Affairs records a major Bhote Koshi River flood in Rasuwa District at **08:40 local time on 26 August 2026**, with severe impacts in riverbank areas of Rasuwa, Nuwakot, Dhading and Gorkha and immediate search, rescue and relief operations.

WHO Nepal separately records severe flash floods beginning on 26 August, health-service disruption and emergency medical support. WHO says the upstream trigger was still being assessed and describes a possible ice-avalanche / temporary-damming mechanism only as preliminary information.

Why this is the best first specimen:

- it is genuinely unscheduled and needs no fabricated Canonical occurrence;
- the authoritative local event time is exact and uses `Asia/Kathmandu`, exercising a UTC+05:45 IANA timezone rather than a whole-hour offset;
- it separates real-world event time from WORLD SIGNALS observation time and source-publication date;
- it is strongly evidenced by first-party government and WHO material;
- it tests cross-domain tagging without requiring a causal interpretation;
- the uncertain upstream trigger can be deliberately omitted rather than promoted into fact;
- the later 4 September UN flash appeal is clearly related but is a distinct downstream institutional development, so AW can test restraint by not manufacturing a story object on the first population tranche.

### 2. DRC Bundibugyo Ebola outbreak — held

WHO provides excellent current epidemiological evidence and repeated dated snapshots. It would test data-as-of semantics, retrospective revision, multi-jurisdiction transmission and repeated-observation identity.

That is precisely why it is not first. An ongoing epidemic would immediately pressure state snapshots, revision chains and story identity simultaneously. AW should establish the smallest real production grammar before importing a large evolving epidemiological series.

### 3. Policy/geopolitical development — held

Current geopolitical developments are analytically valuable but often arrive with contested attribution, fast-changing claims and multiple competing official narratives. They are better used after the factual-observation and evidence-time contracts have survived a lower-ambiguity real case.

### 4. Economic data revision — held

Japan household-spending revisions already helped shape AV's external-revision semantics. Using them first would over-weight a DATA_RELEASE grammar already heavily exercised in Analysis and would blur the question of whether the Live layer can represent genuinely unscheduled developments.

### 5. Market observation — held

Market observations require a separate rights contract before public projection and careful measurement-window semantics. They should not be the first population object.

## Contract pressure found

AV says source-publication time belongs to Live evidence, but v0.1 does not mechanically validate it. Nepal's official sources are published on civil dates rather than requiring fabricated publication timestamps.

AW therefore adds a required evidence `publication_time` object with explicit precision:

- `EXACT_TIMESTAMP`;
- `CIVIL_DATE`;
- `UNKNOWN`.

A civil publication date cannot be upgraded to a clock time. This is the evidence-side analogue of the event-time precision discipline already present in Live Intelligence.

## Controlled population opening

Live Intelligence advances from v0.1 foundation to v0.2 controlled population.

The v0.2 population policy permits:

- production observations: yes, but bounded;
- evidence population: yes, but bounded;
- maximum observations in this tranche: 1;
- maximum evidence rows in this tranche: 2;
- automatic ingestion: no;
- public observation projection: no;
- retrospective migration of Analysis evidence: no.

The AV foundation checkpoint remains frozen inside the v0.2 schema so history is preserved while the live descendant grows.

## Selected observation

`WSLI-RISK-NPL-FLOOD-20260826-001`

Classification:

- type: `PHYSICAL_SHOCK`;
- verification: `PRIMARY_CONFIRMED`;
- jurisdiction: Nepal;
- region: South Asia;
- canonical links: none;
- event local time: `2026-08-26T08:40:00`;
- event timezone: `Asia/Kathmandu`;
- event UTC: `2026-08-26T02:55:00Z`;
- domains: climate/physical risk, health/biosecurity and institutions.

The observation records the flood and immediate official response. It does not encode the possible upstream ice-avalanche / temporary-damming mechanism as a causal fact because official assessment remained ongoing.

## Evidence

Exactly two first-party records:

1. Government of Nepal, Ministry of Home Affairs — Official Disaster Relief Appeal, civil publication date 27 August 2026.
2. World Health Organization, Nepal — emergency-funding / health-response release, civil publication date 30 August 2026.

Both have `canonical_provenance_effect = NONE`.

## Public surface

AW keeps observation projection closed.

The static projection may expose only curated-store metadata:

- schema / data versions;
- internal observation count;
- internal evidence count;
- public observation count = 0;
- runtime-feed claim = false.

The first internal observation is not permission to market the static site as a live news feed.

## Explicit non-goals

AW does not:

- create a Canonical flood event;
- create a story ID;
- add the 4 September UN appeal as a second observation;
- infer the flood's upstream cause;
- populate Ebola observations;
- add market data;
- review Japan household spending in Analysis;
- mutate Source/Change Monitor configuration;
- mutate Analysis;
- enable automatic Canonical commits;
- write Google Calendar;
- auto-merge.

## Next pressure after AW

After this specimen merges, audit whether the second real Live Intelligence case should stress **repeated state snapshots / revisions**. The DRC Bundibugyo Ebola outbreak is a strong candidate because it would force the layer to distinguish a developing story from successive evidence-backed as-of observations without silently overwriting history.