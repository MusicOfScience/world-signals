# BX — China NBS native Latest Releases RSS validation v0.1

Reference date: 2026-09-09  
Frozen base: `29b71bea42610992ad073b1583be64ced7e5de81`

## Source identity correction

The first materialised preflight failed closed before governed acceptance because the proposed machine source ID `WSSRC-MAC-026` was already occupied by an existing Bank of Japan source. No governed post-state was committed.

The registry was re-audited and `WSSRC-MAC-031` was confirmed unused. BX therefore uses:

- Canonical schedule source: `WSSRC-MAC-007` — unchanged;
- monitor-only native RSS source: `WSSRC-MAC-031`;
- route: `CHINA_NBS_LATEST_RELEASES_RSS`.

The successful ordinary-file correction transaction was run `34278500477`, job `102237308887`, producing commit `ad1c6eaf340954634c4e3945d68ec2954c181e7d`. Earlier failed correction harness runs did not push a correction commit and did not modify `main`.

## Materialised preflight

Run `34278772908`, job `102238196152`: **SUCCESS**.

The ephemeral checkout:

- verified `main` remained exactly `29b71bea42610992ad073b1583be64ced7e5de81` and the branch merge-base was exact;
- froze protected data-layer hashes and the complete `WSSRC-MAC-007` source object;
- ran the BX helper in check-only mode;
- materialised the governed BX post-state locally behind `WORLD_SIGNALS_APPLY_MONITOR_BX=1`;
- proved the mutation boundary was exactly five files:
  1. `data/sources/registry.json`
  2. `data/monitor/expectations.json`
  3. `scripts/run_live_monitor.py`
  4. `scripts/run_adapter_smoke.py`
  5. `src/world_signals/adapters/__init__.py`
- proved Canonical remained v0.41 / 689;
- proved Sources materialised as v1.97 / 253;
- proved Monitor expectations materialised as v0.22 / 20;
- proved `WSSRC-MAC-007` remained byte-for-byte semantically identical as an object;
- proved `WSSRC-MAC-031` had zero Canonical dependencies and monitor-only provenance;
- proved the new route configured exactly 36 Canonical occurrences, one native RSS request and zero follow-ups;
- proved all schedule/clock/lifecycle/certainty/write authority gates remained false;
- passed `validate_registry.py`, `validate_live_intelligence.py`, `validate_analysis.py`, the full Python unit-test suite, Python compilation, JavaScript syntax checks and the static build;
- proved protected data-layer hashes remained identical;
- restored the five locally materialised files and finished byte-clean.

The temporary materialised-preflight workflow was removed after success.

## Production-shaped live preflight

Run `34278923786`, job `102238693884`: **SUCCESS**.

Exactly one request was made to the selected native NBS RSS endpoint:

`https://www.stats.gov.cn/sj/zxfb/rss.xml`

Observed live snapshot:

- HTTP 200;
- content type `text/xml`;
- 4,496,148 bytes;
- SHA-256 `b15a457fffcba22c65104d35e1c2dfa9021c6c8ec1b47034c153a152c3db12e7`;
- 500 parsed RSS items;
- 243 items classified into the bounded NBS target-series grammar;
- recent known identities for August 2026 PMI and July 2026 CPI/PPI remained present and deterministic;
- zero review candidates in this pre-release snapshot;
- 244 observations, including the explicit finite-feed absence/no-event-state observation.

Network audit:

- native RSS requests: 1;
- annual schedule requests: 0;
- English RSS requests: 0;
- article follow-ups: 0;
- data API follow-ups: 0;
- search/discovery requests: 0.

Authority audit:

- schedule authority: false;
- clock authority: false;
- lifecycle authority: false;
- certainty authority: false;
- automatic Canonical commit: false;
- Canonical clock mutation: false;
- Google Calendar write: false.

The live comparator accepted only configured identities and retained publication metadata as non-authoritative review evidence. Zero candidates at this snapshot was not interpreted as delay, cancellation, lifecycle state or certainty evidence.

The temporary live-preflight workflow was removed after success.
