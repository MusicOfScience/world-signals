# WORLD SIGNALS — BW Japan CPI activation audit v0.1

Reference date: 2026-09-09  
Exact base `main`: `b277939bc6c540d0986f298a832c7d63a29a2d19`  
Governed transaction head before this audit note: `9c9ecd8e8b015acfb838ceb8c6ae31b708fabe68`

## Governed transition

- Canonical Registry: v0.41 / 689 — unchanged.
- Sources: v1.95 / 252 → v1.96 / 252.
- Monitor expectations: v0.20 / 18 → v0.21 / 19.
- Change Ledger — unchanged.
- Biosecurity — unchanged.
- Live Intelligence — unchanged.
- Analysis — unchanged.
- Automatic Canonical commit — OFF.
- Google Calendar writes — OFF.

`WSSRC-MAC-014` is reused rather than duplicated. Canonical provenance, rights/licence metadata, institution, jurisdiction, registered schedule URL, dependency count and separate official 08:30 JST clock-rule provenance remain unchanged. Only bounded automation/readiness metadata advances.

## Materialised preflight

Run `34252468088`, job `102149985038` — SUCCESS.

The runner-only BW post-state passed:

- exact post-BV ancestry;
- exact five-file materialisation boundary;
- registry, Live Intelligence and Analysis validators;
- full Python unit-test suite (1,055 tests);
- Python compilation;
- JavaScript syntax checks;
- static-site build;
- protected-layer hash equality;
- byte-clean restoration.

The only earlier full-suite failures were two P1-F historical-state compatibility assertions expecting the 4 September Japan-CPI automation state forever. P1-F was repaired narrowly: its historical plan remains unchanged, while its current-state compatibility helper accepts the later BW promotion only when the exact bounded Japan-CPI route and all no-write/no-authority gates are present.

## Production-shaped live preflight

Run `34252589032`, job `102150384155` — SUCCESS.

Exactly two real Statistics Bureau requests were executed:

1. `https://www.stat.go.jp/robots.txt`
2. `https://www.stat.go.jp/english/data/cpi/1582.htm`

Observed evidence:

- robots HTTP 200, `text/plain`, 39 bytes, SHA-256 `dc16c6da46eabfd2aa4db11413b51d3c17e8217bfe59545fca0372adc4bec170`;
- schedule HTTP 200, `text/html`, 13,839 bytes, SHA-256 `09bad0238470a50763a480c56910d642496902956682268e3122ffd3537d1262`;
- 15 national schedule rows parsed;
- 7 configured Canonical reference periods matched exactly;
- 8 parsed national periods were outside configured scope and remained observation-only;
- 0 missing configured rows;
- 0 review candidates;
- 0 follow-up requests;
- no clock, schedule-mutation, lifecycle or certainty authority;
- no repository writes from the live-request step.

The full governed repository gate then passed and the runner restored byte-clean.

## Controlled transaction

Run `34252931849`, job `102151518275` — SUCCESS.

The transaction:

1. re-pinned `main` and merge-base to `b277939bc6c540d0986f298a832c7d63a29a2d19`;
2. froze protected-layer hashes and the exact pre-transaction Japan-CPI source/Canonical scope;
3. executed the guarded check-only helper;
4. materialised exactly five governed/runtime files;
5. asserted Sources v1.96 / 252 and Monitor v0.21 / 19 with Canonical v0.41 / 689 unchanged;
6. proved rights/provenance and the separate clock-rule source remained unchanged;
7. reran validators, 1,055 tests, compilation, JavaScript checks and static build;
8. proved protected layers byte-identical;
9. removed generated outputs;
10. removed every temporary `bw-*` workflow, including the transaction itself;
11. audited the exact staged transaction set;
12. re-fetched and re-pinned `main` immediately before commit;
13. committed and pushed `BW: activate Japan CPI release-schedule monitor`;
14. audited the pushed branch and clean workflow state.

The governed transaction commit is `9c9ecd8e8b015acfb838ceb8c6ae31b708fabe68`.

## Final route contract

Adapter: `JAPAN_CPI_RELEASE_SCHEDULE`  
Source: `WSSRC-MAC-014`

- configured Canonical occurrences: exactly `WSO-MAC-A-0050` through `WSO-MAC-A-0056`;
- request budget: 2;
- robots requests: 1;
- schedule requests: 1;
- follow-up requests: 0;
- schedule mutation authority: false;
- clock authority: false;
- lifecycle authority: false;
- certainty authority: false;
- Canonical clock mutation: false;
- automatic Tokyo-CPI follow-up: false;
- automatic e-Stat/API follow-up: false;
- automatic data-release/PDF/news/search follow-up: false;
- automatic Canonical commit: false;
- automatic Live Intelligence / Analysis promotion: false;
- Google Calendar write: false.

The schedule monitor is therefore a bounded, review-only **civil-date drift sentinel**. The existing 08:30 JST time remains separately sourced and outside this route's authority.
