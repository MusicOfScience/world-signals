# WORLD SIGNALS — IMD heatwave outlook AT transaction audit v0.2

**Executed:** 2026-09-06
**Exact base:** `92bf6cba7506483dd861680924879b1ded0f4ddc`

## Controlled governed-state mutation

- Canonical Registry: `v0.37 / 687` → `v0.38 / 688`
- Source Registry: `v1.79 / 242` → `v1.80 / 243`
- Biosecurity analytical overlay: `v0.12 @ v0.37/687` → `v0.13 @ v0.38/688`
- added occurrence: `WSO-RISK-A-0002`
- added series: `WSER-RISK-IN-HEAT-OUTLOOK`
- added source: `WSSRC-RISK-005`

The overlay advance changes **only** `version` and `canonical_checkpoint`. Systems, relationships, canonical-series memberships, candidate nodes, principles and notes remain semantically unchanged. The IMD outlook receives no biosecurity membership.

## Object boundary

The new occurrence is the **31 March 2026 IMD publication event**. It is not an April–June heatwave season and not an observed heatwave shock. The April–June period remains forecast/reference scope only. No publication clock time or UTC timestamp was invented.

`WSFR-RISK-NIO-TC` remains deferred under `OFFICIAL_SOURCE_DEFINITION_CONFLICT`; AT does not choose April–May versus April–June.

## Coverage result

```json
{
  "totals": {
    "occurrence_count": 688,
    "unique_series_count": 202,
    "unique_institution_count": 127,
    "unique_source_count": 160,
    "occurrences_per_series": 3.41,
    "monetary_plus_macro_occurrence_count": 443,
    "monetary_plus_macro_occurrence_share": 0.6439
  },
  "south_asia": {
    "region": "South Asia",
    "occurrence_count": 29,
    "unique_series_count": 9,
    "unique_institution_count": 7,
    "unique_source_count": 7,
    "unique_category_count": 4,
    "occurrences_per_series": 3.22
  },
  "physical_climate_risk": {
    "category": "PHYSICAL_CLIMATE_RISK",
    "occurrence_count": 7,
    "unique_series_count": 4,
    "unique_institution_count": 4,
    "unique_source_count": 4,
    "unique_category_count": 1,
    "occurrences_per_series": 1.75
  },
  "diagnostic_flags": {
    "regions_with_fewer_than_10_unique_series": [
      "South Asia"
    ],
    "regions_with_fewer_than_8_unique_institutions": [
      "South Asia"
    ],
    "categories_with_fewer_than_5_unique_series": [
      "PHYSICAL_CLIMATE_RISK"
    ],
    "note": "Threshold flags are prompts for qualitative review, not automatic undercoverage findings or population quotas."
  }
}
```

The South Asia and physical-risk mechanical prompts remain open after the correction. This is intentional; AT is not a threshold-clearing transaction.

## Protected-state audit

Protected datasets unchanged: **True**

```json
{
  "before": {
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "monitor_expectations": "d3f40e2aa145c3c292d593ee2096128cd096131e5c9ed0ecc841ee1f982dcb36",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf",
    "analysis_reviews": "d0f2c96be66e150a9c65caf4e7f0c0b3abd10bb0fe239cbe5f56562c52e21e56",
    "analysis_evidence": "56ac1d37fd84c3ab79f4ba23b31342526d8e91447d415732f27fd6dd48c5c3b4"
  },
  "after": {
    "canonical_schema": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
    "change_ledger": "9307c20ef84924934c371633027c091b055158df887854114eee930712b378a2",
    "monitor_expectations": "d3f40e2aa145c3c292d593ee2096128cd096131e5c9ed0ecc841ee1f982dcb36",
    "monitor_operations_policy": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0",
    "analysis_schema": "c71ec08134f3c67e07ce0ef8cf17ec19a626c19487251d65e53f463e48884faf",
    "analysis_reviews": "d0f2c96be66e150a9c65caf4e7f0c0b3abd10bb0fe239cbe5f56562c52e21e56",
    "analysis_evidence": "56ac1d37fd84c3ab79f4ba23b31342526d8e91447d415732f27fd6dd48c5c3b4"
  }
}
```

## Deliberate non-actions

- no Canonical-schema mutation
- no Change Ledger mutation
- no monitor configuration or operations-policy mutation
- no Analysis schema/review/evidence mutation
- no biosecurity semantic-membership mutation
- no `EXACT_TIMESTAMP_SERIES` ingestion
- no future 2027 outlook occurrence
- no North Indian Ocean cyclone-season population
- no automatic canonical commit
- no Google Calendar write
