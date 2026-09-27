# World State production-contract fixture

This directory is a synthetic, test-only contract fixture for Migration Step 7.
It is not a production World State population, Actor Registry, or public
projection.  The test loader derives deterministic object hashes in memory;
the fixture deliberately has no admission transaction and no write target.

Nothing from this directory may be copied into `data/world_state/` as governed
state.  The records use fictional actors, institutions, evidence references,
and dates so the tests cannot become current-world intelligence.
