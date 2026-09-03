# WORLD SIGNALS — GitHub Pages source incident — 2026-09-04

## Summary

The public Pages URL was observed serving the old repository-root/README thin-slice presentation rather than the current Actions-built WORLD SIGNALS web UX.

Observed public symptom:

- page title/content matched the old `WORLD SIGNALS — executable thin slice v0.4` README material;
- the page exposed the old 649-occurrence checkpoint rather than the current v0.20 / 669-occurrence application;
- the same result was reproduced across multiple iOS browsers and a private session, ruling out an ordinary local browser cache explanation.

Repository state at diagnosis:

- canonical registry v0.20 / 669 occurrences;
- source registry v1.51 / 222 sources;
- schema v0.51;
- current `web/` application contains Calendar, Event index, Monitor routes, Operations and Change history views;
- Pages Actions workflow successfully builds the current 669-event application and uploads a `github-pages` artifact.

Additional finding:

- committed `docs/data/events.json` was stale at v0.17 / 649 and there was no repository-root `index.html`;
- this was consistent with Pages being configured to publish from a branch/root rather than the Actions deployment artifact.

User changed repository Settings → Pages → Build and deployment → Source to **GitHub Actions** on 2026-09-04.

A subsequent deploy-job-only retry failed because GitHub Pages artifacts are scoped to the workflow attempt that created them; the deploy step reported `No artifacts named "github-pages" were found for this workflow run.` This is not an application-build failure.

## Required recovery

Trigger one fresh complete `Deploy WORLD SIGNALS web UX` workflow after the Pages source switch so build, artifact upload and deploy occur in the same fresh workflow execution. Then verify the public URL against the generated application itself, not only workflow-green status.

## Prevention

- GitHub Actions is the intended Pages publishing source.
- `web/` + `scripts/build_site.py` are the application source/build path.
- Branch-root README/Jekyll output is not the WORLD SIGNALS application.
- Public endpoint verification is required after significant Pages deployment changes.
- Stale committed `docs/` output should not be treated as authoritative application state.

This incident does not alter the canonical registry, source registry, monitor configuration, review state, automatic canonical-commit gate or Google Calendar-write policy.
