# WORLD SIGNALS — IMD heatwave outlook Analysis AU transaction audit v0.1

- committed_at_utc: `2026-09-06T06:25:45.876473+00:00`
- exact_base_main: `03a8f87f17570c2520edadf78237ed07d946107a`
- occurrence: `WSO-RISK-A-0002`
- new_analysis_id: `WSAN-RISK-IMD-HEAT-OUTLOOK-20260331-001`
- Analysis reviews: `0.15 / 19 -> 0.16 / 20`
- Analysis evidence: `0.15 / 85 -> 0.16 / 91`
- Analysis Canonical checkpoint: `v0.37/687 -> v0.38/688`
- reviewed event-type diversity: `17 -> 18`
- new reviewed event type: `PHYSICAL_RISK_OUTLOOK_RELEASE`
- remaining completed/unreviewed: `WSO-MAC-B-0041`
- production `EXACT_TIMESTAMP_SERIES`: `0`

## Analytical boundary

AU treats the 31 March IMD object as a seasonal risk-information publication. It does not convert April-June into occurrence timing, does not score February MAM versus March AMJ guidance as a matched forecast error, and does not promote later monthly/operational products into proof of seasonal forecast skill.

Later May/June products are retained as forecast-evolution and operational-weather context under `OBSERVATION_CONTEXT / NOT_A_CAUSAL_CLAIM`. IMD-named health, water, power, infrastructure and agriculture channels remain `PLAUSIBLE_WATCH_ITEM`, not observed effects.

## Protected-state audit

All Canonical, Source, Change Ledger, overlay, monitor and Analysis-schema hashes remained unchanged during the controlled Analysis write.

```json
{
  "canonical_registry": "58136692f8df1a2298af9df2a10a8548a2b32666a1f20034fad0945b7fc07c08",
  "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
  "source_registry": "54ac5376777bd9518ecffed06cb80f7c172c218b2c57e7a2f95b8540ebcfd524",
  "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
  "biosecurity_overlay": "e2cc2b48dd6dd680bcb0cab9bd93367c58a3fa45ddf8b8ad53bab4a18e8115c5",
  "monitor_expectations": "d3f40e2aa145c3c292d593ee2096128cd096131e5c9ed0ecc841ee1f982dcb36",
  "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
  "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf"
}
```

## Deliberate non-actions

- no Canonical or Source Registry mutation
- no Change Ledger mutation
- no biosecurity overlay mutation
- no monitor configuration mutation
- no Analysis schema mutation
- no market-response fabrication
- no forecast-skill score
- no future IMD recurrence
- no Google Calendar write
- no auto-merge
