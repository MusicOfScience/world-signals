# WORLD SIGNALS — NHC Atlantic season CF endpoint probe v0.1

This is a bounded endpoint/semantic probe. It does not create a Monitor route or mutate Canonical data.

## Boundary

- OPEC remains quarantined and is unrelated to this route.
- NHC climatology is treated as the semantic authority for the official Atlantic season definition.
- NHC RSS is operational corroboration only; storm/feed activity is never evidence that the official June 1 / November 30 season boundary changed.
- No fetched source body is persisted.

## Canonical targets

- `WSO-COM-A-0049` — Atlantic hurricane season 2026; lifecycle `ACTIVE`; start `2026-06-01`; end `2026-11-30`; source `WSSRC-RISK-002`.
- `WSO-COM-A-0050` — Atlantic hurricane season 2027; lifecycle `PLANNED`; start `2027-06-01`; end `2027-11-30`; source `WSSRC-RISK-002`.

## Endpoint results

| Endpoint | HTTP | Type | Bytes | SHA-256 |
|---|---:|---|---:|---|
| climatology | 200 | text/html; charset=UTF-8 | 60678 | `b0002d85609d1d9aa43ed2704da38216fa942d4f7216231ec4b9fc81c8b910e2` |
| rss_directory | 200 | text/html; charset=UTF-8 | 70092 | `ab71d9a46dc7c65bf212faececd0024feb93cb8610f26f14eaa34babc8501985` |
| atlantic_outlook_rss | 200 | text/xml | 1626 | `8a94edb04ee058d6316fab71b2d65527117c26329b8637850c06d8d3df90af27` |
| atlantic_basin_rss | 200 | text/xml | 2091 | `2f732a5d7e96f162855a93ed93c2ad096a7f5b171dac07a6873c00c2cb0ae84c` |
| robots | 200 | text/plain; charset=UTF-8 | 46 | `2fb8cf32fee88638246fb9e9637eddf72ddb9161e3d5d30a20e77ca602ee36fd` |
| rights | 200 | text/html; charset=UTF-8 | 41616 | `701f917c4bf9fdc15468dad889054c51c02d7c28b81045f7fe20a3c0cc201098` |

## Semantic checks

- climatology_has_atlantic_june1_nov30: **PASS**
- rss_directory_identifies_atlantic_outlook_feed: **PASS**
- rss_directory_identifies_atlantic_basin_feed: **PASS**
- atlantic_outlook_is_machine_readable: **PASS**
- atlantic_outlook_current_payload_has_season_semantics: **NO**
- atlantic_basin_is_machine_readable: **PASS**
- rights_page_has_public_domain_marker: **PASS**

## Route assessment

- climatology machine retrieval viable: **True**
- RSS-only route permitted: **False**
- paired candidate route viable: **True**
- positive evidence: semantic baseline drift may create a review candidate only; no direct Canonical mutation.
- negative evidence: RSS absence, no active storms, or feed failure is source-health evidence only.
