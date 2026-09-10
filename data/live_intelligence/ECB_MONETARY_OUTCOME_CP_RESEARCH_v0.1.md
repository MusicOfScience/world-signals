# CP — ECB monetary-policy outcome research v0.4

## Status

**PRIMARY ECB OUTCOME RECOVERED / PRODUCTION PLAN FROZEN / PREWRITE CONTRACT GREEN / NO GOVERNED POPULATION YET**

CP remains based on exact post-PR #123 `main` commit `e1f5c97c183381f7d29bf6957aecd87cacaa96a0`. This file preserves both the earlier retrieval failures and the later first-party breakthrough; those failures are part of the research history and are not rewritten as though the outcome had always been available through the normal HTML/search surfaces.

## Why CP was selected

The post-CO pressure audit left Europe as the only Canonical region without a Live specimen, but that zero was only diagnostic. CP was selected conditionally because the 10 September 2026 ECB monetary-policy decision is independently systemically important, already belongs to a stable scheduled Canonical family, and can exercise a controlled scheduled `OUTCOME_OF` Live contract. Regional diversification is a benefit, not the selection rule.

## Exact Canonical identity

Identity-aware inspection of the post-#123 Canonical registry resolves the decision as:

- occurrence: `WSO-ad4d0618a65059f2`
- series: `WS.CB.ECB.MONETARY_POLICY_DECISION`
- name: `ECB Governing Council monetary policy decision — 2026-09-10`
- category: `MONETARY_FINANCIAL_POLICY`
- subcategory: `MONETARY_POLICY_DECISION`
- region: `Europe`
- jurisdiction: `Euro area`
- institution: `European Central Bank`
- timing type: `LOCAL_DATETIME`
- native time: `2026-09-10T14:15:00`
- native IANA timezone: `Europe/Berlin`
- canonical UTC: `2026-09-10T12:15:00Z`
- precision: `MINUTE`
- time status: `CONFIRMED`
- time basis: `AUTHORITATIVE_STANDARD_PUBLICATION_RULE`
- schedule source: `WSSRC-CB-003`
- primary schedule assertion: `WSA-901c19618e13196f`
- lifecycle in merged `main`: `PLANNED`
- certainty: `CONFIRMED`
- parent meeting window: `WSO-b2fa91dfcbae5c38`
- related occurrence: `WSO-90f504a4e4925486`, which remains a separate linked event.

The transaction must preserve this identity and every Canonical timing field. It must not create a duplicate occurrence or overwrite the native clock from Live evidence.

## Source roles and governance

### `WSSRC-CB-003` — schedule authority

ECB Governing Council meeting calendar:

`https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html`

This remains the schedule source for the Canonical family.

### `WSSRC-CB-004` — outcome authority

ECB monetary-policy decision/account publication family:

`https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html`

Current repository governance permits curated factual provenance but does **not** grant production unattended retrieval:

- `canonical_provenance_use`: `CLEARED_CURATED_FACTUAL_METADATA`
- `automated_monitoring_use`: `ENDPOINT_REVIEW_REQUIRED`
- `verification_mode`: `MANUAL_AUTHORITATIVE_RECHECK`

The successful read-only research probe does not change those permissions and does not authorise an ECB Monitor route.

## Retrieval history — fail closed before primary evidence

### Initial preflight

Before the scheduled release, ECB official pages stated:

- Governing Council monetary-policy meeting: 9–10 September 2026 in Berlin;
- monetary-policy decisions scheduled for 14:15 Europe/Berlin on 10 September;
- press conference scheduled for 14:45;
- macroeconomic projections later that afternoon.

No outcome row was prepared from schedule passage. The scheduled clock was never treated as completion evidence.

### Post-release rechecks

After 14:15 Europe/Berlin, the normal official HTML/search surfaces remained stale. The decision index continued to expose 23 July as the latest retrievable decision and the 10 September press-conference surface still rendered pre-release material. A bounded Bundesbank/Banque de France cross-check also failed to expose the new decision text.

Contemporaneous secondary reporting indicated that a decision had occurred, but CP did not admit that reporting as a substitute for the registered ECB primary outcome source. No rate payload, Canonical completion or Live observation was authorised from secondary evidence.

The ECB press RSS route was identified at:

`https://www.ecb.europa.eu/rss/press.html`

The ordinary research path could identify the feed but could not inspect the RSS payload because of the MIME/retrieval limitation. That limitation was recorded as a tooling problem, not as evidence that the decision did not exist.

## First-party breakthrough — read-only Actions probe

A temporary GitHub Actions research workflow was introduced with **`contents: read` only**. It had no permission or code path to mutate Canonical, Change Ledger, Monitor, Live, Analysis or Calendar state. Its sole purpose was to fetch ECB first-party surfaces and upload disposable research artifacts.

### Probe run `34499129443`

The ECB press RSS feed returned successfully and exposed exact 10 September first-party links, including:

- decision: `https://www.ecb.europa.eu/press/pr/date/2026/html/ecb.mp260910~314e508016.en.html`
- monetary-policy statement: `https://www.ecb.europa.eu/press/press_conference/monetary-policy-statement/2026/html/ecb.is260910~6a45359cfc.en.html`

This proved that the earlier blocker was propagation/retrieval in the normal research surfaces, not absence of an ECB publication.

### Probe run `34499242250`

The read-only probe followed those exact ECB links and recovered the authoritative outcome.

ECB RSS metadata for the exact decision item:

- title: `Monetary policy decisions`
- publication: `Thu, 10 Sep 2026 14:15:00 +0200`
- UTC: `2026-09-10T12:15:00Z`

ECB RSS metadata for the exact monetary-policy statement:

- publication: `Thu, 10 Sep 2026 15:00:00 +0200`
- UTC: `2026-09-10T13:00:00Z`

The ECB decision page states that the Governing Council **raised all three key ECB interest rates by 25 basis points**. The new rates are:

- deposit facility: **2.50%**
- main refinancing operations: **2.65%**
- marginal lending facility: **2.90%**

The decision specifies that these rates apply **with effect from 16 September 2026**. The monetary-policy statement independently repeats the 25-basis-point decision.

No secondary source is needed for the CP factual outcome.

### Probe run `34499606294` — exact repository prestate

A final read-only probe froze the branch prestate before transaction design:

- Canonical Registry: `v0.42 / 689`
- Source Registry: `v2.04 / 258`
- Change Ledger: `v0.28 / 63`
- biosecurity overlay: `v0.17`, checkpointing Canonical `v0.42 / 689`
- Live schema/observations/evidence: `v0.11 / 10 observations / 14 evidence rows`
- ECB target lifecycle: `PLANNED`
- target last successful assertion: `WSA-901c19618e13196f`
- target last verified: `2026-09-02`
- target related documents: none.

Probe artifact `10161268742` has digest `sha256:d58df81beb0fa930dff1fcb25e222e9504521d8d497d34eeae9f32bdfffc8983`.

## Factual scope admitted to CP

CP admits only the policy-decision facts directly established by the ECB:

1. all three key ECB rates were increased by 25 basis points;
2. the resulting rates are 2.50%, 2.65% and 2.90%;
3. the new rates take effect on 16 September 2026;
4. the exact decision publication is first-party ECB evidence and its 14:15 +0200 publication time is supplied by the ECB's own RSS item for that exact URL.

CP deliberately does **not** fold the following into the Live observation:

- staff macroeconomic projection values;
- press-conference Q&A or interpretation;
- analyst expectations;
- surprise classification;
- asset-price or market reaction;
- causal attribution;
- second-order analysis.

Those remain separate source/event or Analysis questions if later justified.

## Lifecycle architecture decision

The existing Live contract correctly refuses an `OUTCOME_OF` observation against a `PLANNED` Canonical anchor. CP therefore freezes a two-stage governed transaction inside the tranche:

1. **Stage 1 — Canonical lifecycle:** update the existing occurrence `PLANNED → COMPLETED` using the ECB first-party decision publication; append status history and Change Ledger provenance; preserve stable identity, timing, certainty and sensitivity fields; do not add or modify a Source Registry identity.
2. **Stage 2 — Live outcome:** only after Stage 1 yields a validated `COMPLETED` anchor, add one bounded `PRIMARY_CONFIRMED` `POLICY_DEVELOPMENT` observation linked `OUTCOME_OF` `WSO-ad4d0618a65059f2`.

The two stages may be committed by one guarded transaction only after ordered simulation proves that no committed state can contain a Live `OUTCOME_OF` row against the still-`PLANNED` anchor.

Frozen production artifacts:

- `data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PRODUCTION_PLAN_v0.1.json`
- `data/live_intelligence/ECB_MONETARY_OUTCOME_CP_PAYLOAD_v0.1.json`
- `src/world_signals/ecb_monetary_outcome_cp.py`
- `tests/test_ecb_monetary_outcome_cp.py`

## Prewrite validation

The first full prewrite run, `34500135027`, failed closed before any governed mutation because of two defects in the newly written CP test code: one literal-word expectation did not match the already-bounded payload wording, and the test treated the overlay validator's returned error list as an object. Neither failure exposed a governed-data or transaction-semantic defect.

The test assumptions were repaired narrowly. Full prewrite run `34500457145` then passed:

- Canonical validator;
- Live validator;
- Analysis validator;
- derived-state check;
- complete historical unittest discovery — **1,321 tests / 68 historical-prestate skips**;
- Python compilation;
- seven JavaScript `node --check` validations;
- static build.

The CP tests specifically prove that Stage 2 rejects a `PLANNED` ECB anchor, stable Canonical timing/identity is preserved in simulation, CM correction/conflict semantics remain intact, Source/Monitor/Analysis populations remain outside scope, public gates remain closed and Live population overflow fails closed.

## Current conclusion

The primary-evidence blocker is cleared and the bounded transaction is **ready for a guarded materialisation attempt**, but no governed CP population has yet been written at this checkpoint.

The next allowed sequence is:

`exact branch/base recheck → temporary one-shot apply helper → temporary guarded workflow → exact prestate → simulation → focused tests → ephemeral/materialised target validation → complete historical suite → compilation/JS/static build → protected-layer hashes → bounded diff → commit only if every gate passes`.

The temporary read-only ECB probe workflow remains temporary infrastructure and must be removed before any merge handoff. Any temporary write-capable workflow/helper introduced for materialisation must likewise be absent from the final PR head.

Automatic Canonical commit remains off outside this explicitly reviewed transaction. Google Calendar write, automatic Monitor→Live, automatic Live→Analysis and public projections remain off. OPEC quarantine remains untouched.
