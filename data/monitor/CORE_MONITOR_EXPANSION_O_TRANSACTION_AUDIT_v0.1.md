# WORLD SIGNALS — Core monitor expansion O transaction audit v0.1

**Applied at:** 2026-09-05T13:57:59.261527+00:00  
**Research identity probe:** GitHub Actions run `33969711355` — 19/19 exact ONS identities, 0 datetime mismatches.

## Pre → post

- canonical registry: v0.28 / 674 → **unchanged**
- source registry: v1.69 / 233 → **v1.70 / 233**
- monitor expectations: v0.7 / 6 adapters → **v0.8 / 7 adapters**
- automatic canonical commit: **OFF**
- Google Calendar writes: **OFF**

## ONS

Activated `ONS_RELEASE_CALENDAR_RSS` as a read-only review route for the 19 existing ONS canonical dependencies. The route paginates the official upcoming RSS to exhaustion inside a hard bound, matches explicit feed identities, compares scheduled datetime only, and never derives Confirmed/Provisional status from RSS.

Absence/renaming is source-match review evidence only. Elapsed occurrences are not presence-checked against the upcoming feed. No automatic event mutation is authorised.

## Eurostat

Repaired the stored `https://ec.europa.eu/eurostat/en/news/release-calendar` endpoint from misclassified `ICS` to its observed HTML landing-page role. Eurostat automated-monitoring permission remains `CLEARED`, but live activation is held pending recovery and validation of the actual generated `.ics` subscription URL. No HTML scraping route was substituted.

## Protected-file hashes before apply

```json
{
  "data/canonical/registry.json": "295f78bb9bcf495378441d1691afa0ee8085883bff93ef8dfd29f442bcfa3001",
  "data/canonical/schema.json": "0bb71248fd33623531ecfca319e730734425ec0e04b36f72880d42bd489650bd",
  "data/changes/ledger.json": "47fa0467dd6290b867355c18251cd585d61efa885688e7ecfee30a117fb40738",
  "data/coverage/biosecurity_overlay.json": "b6702bde00e5b10e116286c37b11f764376815c7633cd1926d25a61bbc4d41d1",
  "data/monitor/operations_policy.json": "26f16cf67319eb1d91bb936fa74c038cd03ce8d0e580b17d0da91c166741d9b0"
}
```

The transaction does not write any protected file.
