# WORLD SIGNALS — CD first Analysis revision research

**Tranche:** CD  
**Reference date:** 2026-09-09  
**Exact base main:** `c186835d9d6b36620177badfff604f309ceb35d4`  
**Branch:** `feature/post-cc-pressure-audit-cd`

## Pressure-audit result

The post-CC pressure audit does not justify another monitor route by quota. Monitor expectations already contain 25 adapters covering 215 Canonical occurrences, 47 series and all nine configured regions. Live Intelligence remains deliberately bounded at 6 observations / 9 evidence rows and Analysis remains at 21 immutable reviewed snapshots / 95 evidence rows.

The Analysis revision-lineage grammar introduced in BA remains production-closed and has zero production revisions. CD therefore tests whether a real analytical snapshot now has enough evidence pressure to justify the first immutable revision rather than silently editing history.

## Candidate selected

Parent Analysis snapshot:

- `WSAN-BWC-WG8-2026-001`
- Canonical occurrence: `WSO-BWC-WG-2026-S08`
- Canonical series: `WSER-INT-BWC-WG-STRENGTHENING`
- parent `analysis_as_of_utc`: `2026-09-05T19:35:00Z`
- parent second-order status: `PLAUSIBLE_WATCH_ITEM`

The parent packet correctly distinguishes eighth-session procedural consensus from substantive final-package adoption and correctly leaves final consensus unresolved. However, its second-order evidence jumps from the February 2026 eighth session directly to the scheduled December 2026 tenth session. It does not admit evidence from the intervening ninth session, which took place in August 2026.

That omission is analytically material because the parent explicitly defined the next question as whether later Working Group sessions would continue converting the evolving draft into a consensus package. The ninth session is observed follow-through on that exact dependency.

## Newly admitted evidence

### 1. United Nations / UNOG Indico — ninth-session occurrence

URL: `https://indico.un.org/event/1018822/timetable/?view=standard_numbered`

Primary-official event evidence establishes that the ninth session of the Working Group on the Strengthening of the Biological Weapons Convention took place in Geneva from **17–21 August 2026**.

Analytical use: institutional/process follow-through only. It does not establish substantive consensus, adoption, implementation, security effects or market effects.

### 2. Sussex Harvard Information Bank / CBW Events catalogue — ninth-session revised draft identity

URL: `https://shib-temp.cbw-events.org.uk/bwc-wg_plus_msp/`

The specialist institutional catalogue records successive ninth-session draft-final-report artefacts and, in particular, lists **BWC/WG/9/CRP.1/Rev.7**, dated **27 August 2026**, titled **“Revised draft final report of the Working Group on the Strengthening of the Convention”**, linking to the corresponding UNODA Documents Library file.

Analytical use is deliberately narrow: document identity, date and draft-status label only. WORLD SIGNALS does not infer agreement on individual passages from highlight colours, revision number, document length or the existence of the document.

Primary document URL retained for provenance/navigation only:

`https://docs-library.unoda.org/Biological_Weapons_Convention_-Working_Group_on_the_strengthening_of_the_ConventionNinth_session_(2026)/2026-08-27_BWC_WG_9_CRP1_Rev7.pdf`

The CD research process did not rely on unverified extraction of the PDF body.

### Existing evidence retained

The existing parent evidence `WSEV-BWC-WG10-UNODA-SCHEDULE` remains useful: UNODA schedules the tenth session for **7–11 December 2026**. That continued schedule is consistent with an unresolved process but is not itself proof that no earlier substantive agreement occurred.

## Analytical effect

The parent historical statement about the **eighth session itself** remains intact.

The revision changes the second-order layer:

- from `PLAUSIBLE_WATCH_ITEM`
- to `OBSERVED`

because the later-session continuation that had previously been prospective has now been explicitly admitted as observed evidence.

The revised conclusion remains conservative:

- the ninth session is evidence of continued institutional work;
- the later `Rev.7` identity is evidence that a document still labelled a revised draft final report existed after the ninth session;
- the scheduled tenth session remains a future dependency;
- none of those facts establishes adoption of the Working Group's final consensus package;
- no external geopolitical, security, health or market effect is inferred.

This is therefore a **NEW_EVIDENCE** revision, not a factual correction to the parent occurrence and not a `NEW_LIVE_EVIDENCE` revision.

## Alternatives rejected

### Another monitor route
Rejected for CD. Three Canonical categories still lack configured monitor scope, but the audit explicitly treats these as qualitative prompts rather than quotas. Monitor breadth is no longer the clearest architecture frontier.

### Seventh Live observation
Rejected for CD. A seventh Live specimen would test population expansion, but it would not exercise the already-built, still-unused Analysis revision contract.

### Second production Live→Analysis link
Rejected for CD. The existing Japan FIES bridge remains a useful single controlled link. A second link is less architecturally informative than the first immutable Analysis revision and would create unnecessary simultaneous population pressure.

### RBNZ September OCR revision
Rejected. The subsequently surfaced full September Monetary Policy Statement materially strengthens primary-source grounding of the gradual OCR path but does not clearly change the existing analytical conclusion enough to justify a revision solely for specimen population.

### Australian GDP / later RBA communications
Rejected. Later RBA commentary and further market repricing add context, but intervening inflation, oil/geopolitical and central-bank communication signals make a stronger GDP-specific causal revision inappropriate.

## Required CD governance

CD may open the existing Analysis revision contract only to one production revision:

- schema mode: `CONTROLLED_REVISION_LINEAGE`
- `production_analysis_revisions_allowed = true`
- `maximum_production_analysis_revisions = 1`
- `maximum_children_per_revision_parent = 1`
- public revision metadata projection remains false
- automatic latest-Analysis selection remains false
- parent snapshot remains present and byte-semantically unchanged
- Canonical, Calendar, Monitor, Live Intelligence and Source Registry remain unchanged
- no automatic revision creation
- no merge or auto-merge

Any second production Analysis revision requires a new pressure audit.

## Diagnostic history preserved

The first CD post-CC audit failed only in a reporting renderer after the exact baseline and monitor-coverage computation had passed: JSON key sorting encountered mixed `None`/string keys. No governed data changed. The corrected audit passed.

The Analysis revision frontier diagnostic then confirmed:

- Analysis `v0.17 / 21 reviews / 95 evidence`
- production Analysis revisions: `0`
- production Live→Analysis review IDs: only `WSAN-JP-FIES-202607-001`
- Live Intelligence `v0.6 / 6 observations / 9 evidence`
- current Live and Analysis validators PASS
- governed layers unchanged versus the post-CC main baseline.
