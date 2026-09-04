# WORLD SIGNALS — Biosecurity Cross-Domain Overlay Audit v0.1

**Reference date:** 2026-09-04  
**Canonical checkpoint:** v0.20 / 669 occurrences  
**Source registry:** v1.51 / 222 sources  
**Overlay:** `data/coverage/biosecurity_overlay.json` v0.1  
**Canonical mutation authorised:** **NO**  
**Event population authorised:** **NO**

## Purpose

This audit records the implementation and deployment of a non-exclusive biosecurity analytical/coverage overlay. It addresses the structural problem identified by the health/biosecurity coverage audit without falsifying canonical category diversity.

The overlay is **not** part of canonical event identity, timing, lifecycle or primary category. It is a derived system map keyed to stable canonical series where such series actually exist.

## Mechanical baseline

The read-only diagnostic run `33817225156` established that canonical `HEALTH_BIOSECURITY` at v0.20 contains:

- **10 occurrences**;
- **5 series**;
- **1 institution: World Health Organization**.

The five canonical WHO series are:

- `WSER-HEALTH-WHA`;
- `WSER-HEALTH-WHO-EB`;
- `WSER-HEALTH-WHO-IGWG`;
- `WSER-HEALTH-WHO-PBAC`;
- `WSER-HEALTH-WHO-RC`.

The same diagnostic found **zero canonical adjacent matches** for WOAH, IPPC/CPM, BWC/UNODA, Africa CDC or One Health. Therefore the WHO concentration is genuine at this checkpoint and is not repaired by relabelling already-existing non-WHO holdings.

Durable diagnostic evidence: `data/coverage/BIOSECURITY_TAXONOMY_DIAGNOSTIC_v0.1.md`.

## Cross-domain system model

The overlay defines four non-exclusive analytical systems:

1. `BIO-HUMAN-HEALTH-GOVERNANCE` — human-health governance;
2. `BIO-ANIMAL-ZOONOTIC-HEALTH` — animal and zoonotic health;
3. `BIO-PLANT-PHYTOSANITARY-SECURITY` — plant and phytosanitary security;
4. `BIO-BIOLOGICAL-SECURITY-ARMS-CONTROL` — biological security and arms control.

`ONE_HEALTH` is deliberately a **CROSS_CUTTING relationship**, not another primary bucket. It links human, animal and plant systems without asserting that every event in those systems is itself a One Health event.

## Canonical memberships

Only the five WHO series that actually exist are mapped, all to `BIO-HUMAN-HEALTH-GOVERNANCE`.

The overlay does not change their canonical primary category (`HEALTH_BIOSECURITY`), institution, timing, lifecycle, source or identity.

Current mapped footprint:

- human-health governance: **5 canonical series / 10 occurrences**;
- animal and zoonotic health: **0 canonical series**;
- plant/phytosanitary security: **0 canonical series**;
- biological-security/arms-control: **0 canonical series**.

This asymmetry is intentional evidence, not a defect to hide.

## Noncanonical candidate nodes

Four research nodes are represented without canonical `series_id` or `occurrence_id`:

- `BIO-CAND-WOAH` — World Organisation for Animal Health;
- `BIO-CAND-IPPC-CPM` — International Plant Protection Convention / Commission on Phytosanitary Measures;
- `BIO-CAND-BWC` — Biological Weapons Convention / UNODA;
- `BIO-CAND-AFRICA-CDC` — Africa Centres for Disease Control and Prevention.

Their institutional-role basis is grounded in current official institutional material:

- WOAH: https://www.woah.org/en/who-we-are/
- IPPC: https://www.ippc.int/en/about/overview/
- BWC / UNODA: https://disarmament.unoda.org/en/our-work/weapons-mass-destruction/biological-weapons/biological-weapons-convention
- Africa CDC: https://africacdc.org/about-us/

These role descriptions establish analytical relevance only. They do not establish event timing, source rights, monitorability or canonical admission.

## Executable safeguards

`src/world_signals/analytical_overlays.py` validates that:

- mapped canonical series actually exist;
- mapped institution and primary category exactly match the canonical registry;
- candidate nodes carry no canonical occurrence/series identities;
- candidate institutions becoming canonical forces overlay review rather than silent duplication;
- One Health remains cross-cutting;
- the overlay explicitly grants no population or mutation authority.

`src/world_signals/biosecurity_projection.py` creates a browser-safe projection. Regression tests verify the live v0.20 mapping, fail closed on unknown series/category redefinition, preserve canonical immutability, and prohibit browser write paths.

Full project CI passed on commits implementing both the overlay and its public projection.

## UX deployment

The Operations view now contains a **Cross-domain coverage → Biosecurity system map** section.

It visibly distinguishes:

- canonical series/occurrence counts by analytical system;
- noncanonical research nodes;
- One Health cross-cutting relationships;
- the absence of canonical animal, plant and arms-control series.

Candidate nodes are labelled **NONCANONICAL CANDIDATE** and expose only role basis, analytical system, relationship, current status, official institutional link and next gate.

Pages deployment run `33821356707` completed **SUCCESS** after:

- canonical validation;
- Python regression suite;
- JavaScript syntax checks including `web/biosecurity.js`;
- browser-safe runtime/review projections;
- site build;
- Pages artefact upload; and
- deploy.

## Decision

The biosecurity architecture problem is sufficiently resolved for v0.1 analytical coverage work.

Do **not** respond by bulk-populating the four candidate institutions. Each requires its own normal source/timing/rights/importance review. The overlay should evolve only when canonical admission or analytical evidence warrants it.
