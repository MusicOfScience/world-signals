# WORLD SIGNALS — BD Vietnam–Myanmar Live transaction audit v0.1

## Transaction identity

- Governing tranche: **BD — bounded Vietnam–Myanmar geopolitical Live specimen**
- Exact post-BC `main` base: `667d0fbcc92f937b0cb609d619b664a2a97e8165`
- Transaction workflow run: `34037302511`
- Transaction workflow head: `df3b1b464407204b9bfe200d39ae279310fd9cea`
- Governed-state transaction commit: `69ac527a1436075ad328f85fd8dc9f7ef3ce386c`
- Successful workflow self-removal commit: `d3f8c7b8ace028e50887bdc75d03f378c79e2aa6`
- Manual merge only: **YES**
- Auto-merge: **PROHIBITED**

## Selection and source-time boundary

BD admits one current first-party geopolitical development: the Government of Viet Nam report of the 5 September 2026 Viet Nam–Myanmar leaders' meeting and agreement to elevate defence/security cooperation as a bilateral pillar.

The source supplies a publication timestamp equivalent to **2026-09-05T09:16:00Z**, but describes the leaders' meeting only as occurring on Saturday morning. WORLD SIGNALS therefore stores the event itself at **CIVIL_DATE 2026-09-05** and does not convert the publication clock time or the phrase “Saturday morning” into a fabricated event timestamp.

The observation has no pre-existing Canonical occurrence identity. BD therefore leaves `canonical_links` empty rather than manufacturing a summit occurrence after the fact.

## Pressure-audit decision

BD was selected over three competing pressures: a BARMM Live backfill merely to exercise `CONTEXT_FOR`, an OPEC outcome before OPEC's own authoritative publication, and a first Analysis revision without evidence sufficient to change a reviewed analytical judgement. Coverage diagnostics remain prompts rather than quotas.

## Governed state

Pre-BD:
- Live Intelligence schema **v0.4**
- Live observations **4**
- Live evidence **6**
- Analysis **21 reviews / 95 evidence**
- production Live inputs **1**
- production Analysis revisions **0**
- production `EXACT_TIMESTAMP_SERIES` **0**

Post-BD:
- Live Intelligence schema **v0.5**
- Live observations **5**
- Live evidence **7**
- population state `CONTROLLED_GEOPOLITICAL_SPECIMEN`
- Analysis remains **21 reviews / 95 evidence**
- production Live inputs remain **1**
- production Analysis revisions remain **0**
- production `EXACT_TIMESTAMP_SERIES` remains **0**

## Authorised governed writes

Exactly five governed paths were mutated:
1. `data/live_intelligence/schema.json`
2. `data/live_intelligence/observations.json`
3. `data/live_intelligence/evidence_registry.json`
4. `PROJECT_STATUS.md`
5. `ROADMAP.md`

This audit file is transaction provenance, not a sixth governed target write.

## Protected layers

Canonical Registry, Canonical schema, Source Registry, Change Ledger, biosecurity overlay, monitor expectations/operations policy and all Analysis data/schema were protected by pre/post SHA-256 comparison and remained byte-identical.

Public Live projection remains closed. Automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. No Source Registry, Canonical, Change Ledger, Monitor or Analysis row was created or changed by BD.

## Validation and descendant repairs

- BA/AZ/BC descendant-safety repair run `34036245528`: **SUCCESS**. Historical checkpoints remain frozen while mutable recovery prose and later reviewed population are not misclassified as drift.
- BD diagnostic preflight v3 run `34036665422`: untouched repository and BD mutation boundary/validators passed; it exposed a stale BB downstream-population ceiling and cleaned up without persistent BD state.
- BB descendant repair run `34037050893`: **SUCCESS**. BB's exact historical Canonical/source/change contribution remains frozen while unrelated later Live/Analysis growth is validated as a descendant floor.
- Decisive BD full two-state preflight v4 run `34037103779`: **SUCCESS**, including untouched full CI/build, ephemeral BD exact five-file mutation proof, full post-BD descendant CI/build and protected-path byte equality.
- Controlled transaction run `34037302511`: **SUCCESS**. Registry, Live Intelligence, Analysis and checkpoint validators passed; the complete repository suite passed **839 tests with 39 skipped**; Python compilation, JavaScript syntax checks and static-site build passed; protected paths remained byte-identical.

## Transaction validation

The transaction materialised BD only after the read-only prestate passed. It re-proved the exact five-file governed mutation set before running the complete descendant suite. Build-only outputs were removed or restored before commit and the tracked write set was re-proved. The static build reported 689 Canonical events, 8 configured monitor routes, 244 governed sources, Live Intelligence v0.5 with zero public observations, and 21 analytical reviews.

## Provenance-document repair

The first generated copy of this audit used an unquoted shell heredoc. Markdown backticks inside that heredoc were interpreted by the shell as command substitutions, stripping several code-formatted identifiers from the audit text. That defect affected **this provenance Markdown only**: it did not change the five governed BD target files, validator results, protected hashes, or transaction state. The audit was therefore corrected directly after transaction completion before the final branch audit and PR.

## Merge policy

The transaction commits only to `feature/post-bc-vietnam-live-bd`. It does not merge itself. A single ordinary pull request and ordinary PR CI remain mandatory; the user performs the merge manually.
