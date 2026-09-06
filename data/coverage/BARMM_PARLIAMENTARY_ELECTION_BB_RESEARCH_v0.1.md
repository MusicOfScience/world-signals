# WORLD SIGNALS — BB BARMM parliamentary election research v0.1

**Reference date:** 2026-09-06  
**Scope:** bounded source + Canonical coverage repair; no Live Intelligence or Analysis population

## Research question

Does the first regular BARMM parliamentary election create a material upstream coverage gap that should be repaired before WORLD SIGNALS adds another Live specimen or exercises the new Analysis revision contract?

## Authoritative timing evidence

### Commission on Elections (COMELEC), Philippines

Primary electoral-authority evidence:

- Certified List of Candidates for the **September 14, 2026 BARMM Parliamentary Elections**.
- URL: `https://www.comelec.gov.ph/php-tpls-attachments/2025BARMMPE/260513_BARMMPE_TentativeCLC/_REGIONAL.pdf`
- The document header explicitly identifies the election date as **September 14, 2026**.
- The source supports polling-day civil-date admission. It does **not** establish a reviewed polling opening/closing clock time for WORLD SIGNALS purposes.

Temporal consequence: store `2026-09-14` at civil-date / day precision in `Asia/Manila`; do not manufacture `start_utc` or a representative midnight timestamp.

## Significance / institutional context

### Office of the Presidential Adviser on Peace, Reconciliation and Unity (OPAPRU)

Official Philippine peace-process material describes the election as the first Bangsamoro parliamentary election and a milestone in the Mindanao peace process:

- `https://peace.gov.ph/2026/04/safe-and-secure-2026-barmm-bske-elections/`
- `https://peace.gov.ph/2026/05/statement-of-secretary-mel-senen-sarmiento-on-the-upcoming-first-parliamentary-bangsamoro-elections-18-may-2026/`
- `https://peace.gov.ph/2026/08/opapru-mobilizes-joint-peace-mechanisms-security-sector-to-safeguard-upcoming-barmm-elections/`

OPAPRU is used here to establish why the omission matters analytically and geographically. It is **not** promoted into a second Canonical timing authority in BB.

## Coverage finding

Repository search on the exact post-BA `main` checkpoint found:

- no BARMM / Bangsamoro parliamentary election occurrence in the Canonical Registry;
- no COMELEC source entry in the governed Source Registry;
- no OPAPRU source entry in the governed Source Registry;
- no existing Canonical occurrence to which a BARMM pre-election Live development could be safely linked.

Therefore a Live `CONTEXT_FOR` relationship would be premature: it would either point to a nonexistent Canonical object or tempt WORLD SIGNALS to smuggle a missing scheduled event through the Live layer.

## Candidate comparison

### First production Analysis revision

**HOLD.** BA created revision capability but no reviewed Analysis packet presently has material later evidence requiring a changed analytical judgement. Exercising revision merely because the contract exists would create artificial analytical history.

### Fifth Live observation — Vietnam / Myanmar defence-security cooperation

**VALID BUT LOWER MARGINAL PRESSURE.** A 5 September 2026 Government News Vietnam report provides a clean first-party geopolitical/institutional development candidate. However, unscheduled Live observations without Canonical links were already exercised by AW/AX. Adding this row would broaden content more than architecture.

### OPEC+ 6 September meeting

**NOT SELECTED AT SCREENING POINT.** At the screening point, contemporaneous reporting described an expected outcome rather than an authoritative completed decision. WORLD SIGNALS must not promote an expectation into a factual outcome.

### BARMM parliamentary election

**SELECTED.** The omission is upstream, imminent and institutionally material. The first regular BARMM parliamentary election is scheduled eight days after the audit reference date, is tied to the Bangsamoro peace-process political transition, and improves Southeast Asia / Global South election coverage. A primary election authority supplies the polling date.

## Source-governance finding

COMELEC's official status and public accessibility establish source authority, not blanket automation or redistribution permission.

BB therefore authorises only:

- manual / curated factual provenance;
- retention of the authoritative URL and minimal factual metadata;
- `PRODUCTION_AUTOMATION_HOLD` pending a separate rights/endpoint review;
- no source-content republication;
- no automatic Canonical commit.

The certified-candidate PDF contains personal/candidate data and an explicit data-privacy notice. WORLD SIGNALS has no need to ingest or republish candidate-level content in this tranche. Only the minimal election-date fact and source identity are retained.

## BB architectural decision

Repair the upstream gap in the established order:

`Source Registry -> Canonical occurrence -> Change Ledger provenance -> derived Calendar/Pages`

Do **not** add:

- Live observations;
- Analysis reviews or revisions;
- monitor adapters;
- automatic source retrieval;
- Google Calendar writes;
- a fabricated clock time or UTC timestamp.

The event will be one explicit `ELECTION_MILESTONE` occurrence at civil-date precision. A later post-BB pressure audit may decide whether BARMM pre-election developments or election outcome evidence justify Live/Analysis work; BB itself does not pre-authorise that expansion.
