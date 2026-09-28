# World State production contract schemas

This directory contains the Migration Step 7 contract schemas and the first
controlled Migration Step 8 production-history population. It contains exactly
one admitted internal Dimension Assessment and one compositional snapshot; it
does not contain a monolithic `state.json`, an Actor Registry population or a
public projection.

Step 11A adds a retained, non-governed RBNZ Analysis specimen under
`data/world_state_audit/`. Its two narrow Dimension Assessment candidates and
proposal-local central-bank identity remain review-pending. The executable
`WORLD_STATE_ACTOR_IDENTITY_ADMISSION` boundary is identity-only and manual-
review-gated; it does not open Actor Registry population or admit actor claims.

Step 11A.1 adds only a corrected successor audit artifact. It does not rewrite
the original specimen or admit production state. Unknown institutional
effective-from is explicit and separate from identity-known-at; source-reported
market windows use the existing civil-date read precision rather than an
invented exact movement timestamp.

The production history is split across `components.json`, `snapshots.json` and
`admission_transactions.json`. Test data belongs under
`tests/fixtures/world_state_production_v1/` and must not be copied here.
