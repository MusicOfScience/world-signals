# World State production contract schemas

This directory contains the Migration Step 7 contract schemas and the first
controlled Migration Step 8 production-history population. It contains exactly
one admitted internal Dimension Assessment and one compositional snapshot; it
does not contain a monolithic `state.json`, an Actor Registry population or a
public projection.

The production history is split across `components.json`, `snapshots.json` and
`admission_transactions.json`. Test data belongs under
`tests/fixtures/world_state_production_v1/` and must not be copied here.
