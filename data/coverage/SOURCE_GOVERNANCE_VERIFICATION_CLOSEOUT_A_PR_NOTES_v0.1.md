# Verification Closeout A — PR notes

This branch is research/infrastructure only. It does not mutate the production canonical registry, source registry, change ledger, monitor expectations, monitor routes, Calendar state or UI.

Review points:

- Fresh post-repair diagnostic starts from 95 P1 sources and rejects mechanical dependency-only selection because the active horizon is geographically concentrated.
- Exactly eight P1 records have `verification_mode` as the only missing governance field and a future canonical dependency.
- Vietnam is held out because direct National Assembly evidence is now better scoped than the currently registered government-news source.
- Seven sources are frozen for Verification Closeout A: APEC, AIIB, Royal Thai Government, Morocco MEF/legal portal, Parliament of South Africa, Philippines PCO and Kenya Law/National Treasury.
- APEC's denormalised stored dependency helper is 0 while canonical truth is 1. The planned transaction repairs that one present mismatch and deliberately does not bulk-fill eight legacy omissions.
- Proposed production transaction remains source-registry-only: v1.61 /224 → v1.62 /224, canonical v0.21 /669 unchanged.
- No monitor route is activated; automatic canonical commit and Google Calendar writes remain false.
- Ephemeral post-state simulation run `33907264111` passed exact one-file enforcement, validation, 244 tests (1 skipped), Python/JS checks and full site build.
- Simulated generic audit: 65 fully explicit /159 missing-any /88 P1 /71 P2; missing provenance 156, automation 156, verification 159.
- This work is intentionally not labelled P1-I.
