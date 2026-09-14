# WORLD SIGNALS — local operations service CW plan v0.1

**Status:** REVIEWED CODE PATH / MACHINE INSTALLATION NOT YET AUTHORISED

**Reference date:** 14 September 2026, Australia/Melbourne

**Exact base:** `652d29c014bae3ac77cfb60b01c81efbfc1e62d3`

## Charter pressure

The Charter requires continuous authoritative-source verification, while the merged local operations runtime currently depends on a person starting each run and separately keeping a loopback server alive. GitHub Actions remains unavailable because of an account billing/spending admission failure. A production local path therefore needs repeatable scheduling without acquiring any governed-layer write authority.

## Bounded change

- Generate two reviewable macOS user LaunchAgent manifests:
  - one daily refresh invoking the existing `scripts/run_local_operations.py` guard stack;
  - one persistent static dashboard server bound only to `127.0.0.1:8765`.
- Preserve the governed `DAILY_BASELINE_WITH_SOURCE_SPECIFIC_SEMANTIC_CADENCE_RECORDED_IN_EXPECTATIONS`; the manager rejects a faster arbitrary cadence.
- Confine run state and logs to ignored `.world-signals-runtime/`.
- Provide read-only render/status paths and separately gated install/uninstall paths.
- Require a clean reviewed `main` checkout before installation.
- Require every scheduled refresh to fail closed unless the checkout is still clean `main` and local `HEAD` exactly equals its tracked upstream head.

## Safety boundary

- This tranche creates and validates service-management code only. It does not install, load, unload or delete a user service during PR validation.
- Installation requires `WORLD_SIGNALS_INSTALL_LOCAL_SERVICE=YES` after the reviewed PR is merged.
- Uninstallation requires the separate `WORLD_SIGNALS_UNINSTALL_LOCAL_SERVICE=YES` gate and removes only manifests whose parsed label matches the controlled WORLD SIGNALS label.
- No automatic Canonical, Source, Change Ledger, Monitor-contract, Live Intelligence, Analysis or Calendar mutation.
- No automatic Git commit, push, PR creation or merge.
- A feature checkout or unsynchronised `main` pauses scheduled refresh rather than publishing unmerged code.
- The dashboard remains loopback-only.
- OPEC quarantine and `HANDOFF_PROTOCOL.md` remain unchanged.

## Gate

- exact manifest and negative-boundary tests;
- render-only inspection of both generated plists and service metadata;
- ordinary full test/validator/build suite at the final committed head;
- protected-path, structural diff and residue checks;
- hosted CI when runnable, otherwise the adopted exact-head local fallback;
- separate user approval before post-merge machine installation.
