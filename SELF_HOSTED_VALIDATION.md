# WORLD SIGNALS — optional self-hosted validation runbook

This runbook is subordinate to `WORLD_SIGNALS_PROJECT_CHARTER.md`, `VALIDATION_POLICY.md` and `HANDOFF_PROTOCOL.md`.

It provides an optional execution route for ordinary WORLD SIGNALS validation when GitHub-hosted runner capacity is unavailable or intentionally conserved. It does **not** move scheduled monitoring, GitHub Pages, Canonical state, Calendar state or any write authority onto the local machine.

## Scope

Only the workflow job `Validate WORLD SIGNALS` can be redirected to the self-hosted runner.

The following remain GitHub-hosted under CR:

- the daily read-only Live Monitor;
- GitHub Pages build/deploy;
- manually invoked standalone coverage diagnostics unless separately changed later;
- any unrelated repository workflow.

The local machine therefore does not need to remain online continuously. Start the runner when WORLD SIGNALS needs validation; stop it afterward.

## Security boundary

A self-hosted runner executes workflow code on the local machine under the permissions of the account/process that runs the runner. Treat it as trusted execution infrastructure.

For WORLD SIGNALS:

- use a repository-level runner dedicated to this private repository;
- do not attach the runner to public/untrusted repositories;
- do not permit untrusted fork pull requests to execute on it;
- do not store registration tokens, credentials, API keys or GitHub-generated setup commands in this repository;
- keep workflow permissions at the minimum required; the ordinary validation workflow uses `contents: read`;
- stop/remove the runner if the machine is lost, transferred or no longer trusted.

## One-time setup

In the WORLD SIGNALS repository on GitHub, open:

**Settings → Actions → Runners → New self-hosted runner**

Choose the operating system and architecture of the machine that will execute validation. Follow **the commands GitHub displays at that time**. The registration token and download version are time-sensitive; this runbook intentionally does not copy them.

When GitHub asks for runner configuration:

- configure it for this repository only;
- give it a clear name identifying the machine without embedding personal secrets;
- add a dedicated custom label: `world-signals-validation`;
- use the default work-folder choice unless there is a concrete reason not to.

GitHub's runner software must remain current enough to accept jobs. Follow GitHub's upgrade guidance when the runner reports that an update is required.

## Required tools

The workflow provisions the language runtimes it needs using GitHub Actions:

- Python 3.13 for every profile;
- Node 24 for `FULL` only.

The host still needs the basics required to run the GitHub Actions runner and checkout workflow, including a supported operating system, network access to GitHub, Git and a suitable shell. Platform-specific runner prerequisites are governed by GitHub's current setup instructions.

## Route validation to the local runner

Create a repository Actions variable:

**Settings → Secrets and variables → Actions → Variables → New repository variable**

Name:

```text
WORLD_SIGNALS_VALIDATION_RUNNER
```

Value:

```text
world-signals-validation
```

The validation workflow resolves its runner as:

```text
WORLD_SIGNALS_VALIDATION_RUNNER if set; otherwise ubuntu-latest
```

This variable contains a runner label only. It is not a secret and must never contain a registration token.

To return ordinary validation to GitHub-hosted compute, remove/unset `WORLD_SIGNALS_VALIDATION_RUNNER`. No repository code change is required.

## Start a validation session

1. Start the registered GitHub Actions runner using the command/method GitHub configured for the host.
2. Confirm GitHub shows the repository runner as **Idle/Online** under Settings → Actions → Runners.
3. Only then open or update the WORLD SIGNALS pull request that needs validation, or rerun its failed ordinary validation job.
4. Inspect the workflow result normally. The selected profile (`FULL`, `SAFE_RESEARCH_DOCS` or `POST_MERGE`) remains part of the exact-head validation evidence.
5. After required work is complete, stop the runner if continuous availability is unnecessary.

Do not make no-op commits merely to trigger a run. Prefer rerunning the existing failed job or making a real final-head change only when required.

## What counts as valid evidence

A successful self-hosted run is ordinary CI evidence only when:

- GitHub Actions executed the repository's `Validate WORLD SIGNALS` workflow;
- the run is attached to the actual final PR head;
- the fail-closed classifier selected the profile from the exact base/head state;
- that selected profile completed successfully;
- the required coverage/pressure evidence was generated in the same run;
- tranche-specific gates, diff/residue checks and `HANDOFF_PROTOCOL.md` requirements also pass.

A manual terminal invocation can be useful development/preflight evidence, but it does not silently replace the GitHub-linked exact-head run required by the current handoff policy.

## Failure modes

If a job remains queued while the self-hosted runner is expected to take it:

- confirm the runner is online;
- confirm its custom label is exactly `world-signals-validation`;
- confirm `WORLD_SIGNALS_VALIDATION_RUNNER` contains the same label;
- confirm the runner is registered to the WORLD SIGNALS repository and is permitted to accept the job;
- inspect GitHub's runner diagnostics before changing repository code.

If the runner is unavailable, removing the repository variable returns future validation jobs to `ubuntu-latest`. That fallback still depends on available GitHub-hosted capacity.

If either execution route cannot run the required validation, retain `DO NOT MERGE`.

## Decommissioning

When self-hosted validation is no longer needed:

1. remove/unset the repository variable `WORLD_SIGNALS_VALIDATION_RUNNER`;
2. remove the runner from repository Settings → Actions → Runners using GitHub's current removal procedure;
3. stop and remove the local runner service/process and working directory as appropriate for the host;
4. verify a later ordinary validation job resolves to `ubuntu-latest` when hosted capacity is available.

Self-hosting is intentionally reversible and is not part of the canonical WORLD SIGNALS architecture.
