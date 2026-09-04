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
- Pages Actions workflow successfully built the current application and uploaded a `github-pages` artifact.

Additional finding:

- committed `docs/data/events.json` was stale at v0.17 / 649 and there was no repository-root `index.html`;
- this was consistent with Pages being configured to publish from a branch/root rather than the Actions deployment artifact.

The repository Pages source was changed to **GitHub Actions** on 2026-09-04.

A deploy-job-only retry then failed because GitHub Pages artifacts are scoped to the workflow attempt that created them; the deploy step reported `No artifacts named "github-pages" were found for this workflow run.` This was not an application-build failure.

## Resolution

A fresh complete `Deploy WORLD SIGNALS web UX` workflow was triggered after the source switch so build, artifact upload and deployment occurred in the same workflow execution.

Fresh workflow run `33819680572` completed with:

- build: **SUCCESS**;
- Pages artifact upload: **SUCCESS**;
- deploy: **SUCCESS**;
- generated application checkpoint: canonical v0.20 / 669 occurrences, six configured monitor routes, 222 governed sources.

The public endpoint was then checked by the user in-browser and confirmed to show the current tabbed WORLD SIGNALS application: Calendar, Event index, Monitor routes, Operations and Change history.

**Incident status: CLOSED.**

## Prevention

- GitHub Actions is the sole intended Pages publishing source.
- `web/` + `scripts/build_site.py` are the application source/build path.
- generated `docs/` output is build-time material and should not be tracked as a competing publication snapshot;
- branch-root README/Jekyll output is not the WORLD SIGNALS application;
- significant Pages changes require public endpoint verification, not only workflow-green status;
- deploy-only reruns must not be used when the required Pages artifact belongs to a different run/attempt.

This incident and its cleanup do not alter the canonical registry, source registry, monitor configuration, review state, automatic canonical-commit gate or Google Calendar-write policy.
