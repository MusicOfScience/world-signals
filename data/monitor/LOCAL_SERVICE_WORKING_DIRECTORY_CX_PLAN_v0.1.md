# WORLD SIGNALS — local service working-directory repair CX plan v0.1

**Status:** POST-MERGE OPERATING REPAIR / SERVICES REMOVED PENDING REVIEW

**Reference date:** 14 September 2026, Australia/Melbourne

**Exact base:** `1db1f90989e7ed457078294a7ea8f775c4aa863e`

## Observed failure

After PR #131 merged, the owner explicitly approved installation of the two reviewed macOS user services. Both LaunchAgents loaded, but neither Python process progressed beyond interpreter startup. The dashboard opened no socket and the automatic refresh produced no run evidence.

A read-only process sample located both processes inside Python's startup working-directory resolution while their LaunchAgent working directory was the repository under `Documents`. This is a macOS privacy boundary, not a monitor, parser, source or governed-data failure.

The two non-functioning jobs and their controlled plist files were removed with explicit approval. Runtime evidence and logs were preserved. No Canonical or other governed population changed.

## Narrow probe

An explicitly approved temporary `launchctl submit` probe started the same Python runtime outside the protected repository working directory while serving the existing built dashboard by absolute path. It returned HTTP 200 on loopback port 8766 and was immediately removed. This disproves the need for Full Disk Access or a duplicate repository.

## Bounded repair

- Use `~/Library/Application Support/WORLD SIGNALS` as the neutral working directory for both user services.
- Keep the reviewed repository, built dashboard, private retained evidence and governed registries in their existing locations.
- Pass the neutral directory into the local runner so every child Python process starts there.
- Invoke all repository scripts by absolute path and provide an explicit repository/root `PYTHONPATH`.
- Invoke Git with `git -C <reviewed-root>` so branch/head guards do not depend on a protected current working directory.
- Preserve the daily cadence, clean-main/upstream gate, loopback-only binding and all automatic-write prohibitions.

## Safety boundary

- Do not grant Full Disk Access or weaken macOS privacy controls.
- Do not install the repaired services before this branch passes exact-head validation and manual merge.
- No automatic Canonical, Source, Change Ledger, Monitor-contract, Live Intelligence, Analysis, Calendar or Git mutation.
- No automatic commit, push, PR or merge.
- OPEC quarantine and `HANDOFF_PROTOCOL.md` remain unchanged.

## Gate

- focused manifest/runner child-process tests;
- ordinary full suite, validators, coverage and build at exact final head;
- generated-plist inspection;
- temporary launchd dashboard probe and exact-head live runner from the neutral working directory;
- clean protected-layer and residue checks;
- hosted CI when runnable, otherwise the adopted exact-head local fallback.
