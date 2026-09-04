# WORLD SIGNALS — P0 source-governance research v0.1

**Reviewed:** 2026-09-04  
**Scope:** five source identities currently used by the six configured live-monitor adapters  
**Canonical mutation authorised:** **NO**  
**Automatic canonical commit:** **OFF**  
**Google Calendar writes:** **OFF**

## Purpose

The source-governance completeness audit found that the five source identities currently used by configured monitors still predate the modern explicit split between:

- `canonical_provenance_use`;
- `automated_monitoring_use`;
- `verification_mode`; and
- `monitoring_readiness_status`.

This research pass assigns those fields only where direct source/route evidence supports the classification. Public accessibility, machine readability, an official domain and successful parser execution are **not** treated as permission evidence by themselves.

This is an operational governance review for WORLD SIGNALS, not a legal opinion.

## Primary-source findings

### Reserve Bank of Australia — `WSSRC-FIN-001`

Primary rights source: <https://www.rba.gov.au/copyright/>

The RBA states that, apart from enumerated excluded material and third-party content, RBA material is provided under Creative Commons Attribution 4.0. The Financial Stability Review monitor uses RBA-owned publication metadata from the official FSR/RSS surfaces rather than reproducing excluded or third-party publication material.

Result:

- curated factual provenance: **cleared**;
- official RSS pilot: remains operationally validated;
- broad automation permission is **not inferred** merely from the CC BY notice, so the modern automation field remains `ENDPOINT_REVIEW_REQUIRED` rather than being overstated as generally cleared.

No source split is needed: the relevant publication and RSS surfaces are part of the same RBA institutional/copyright regime.

### EUR-Lex / Publications Office Cellar — `WSSRC-TECH-001`

Primary reuse source: <https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html?locale=en>

EUR-Lex states that its data may be reused free of charge subject to copyright conditions and explicitly documents machine-access routes including webservices, bulk downloads, database RSS, Cellar REST and the Cellar SPARQL endpoint.

The CRA monitor's primary executable route is the Publications Office Cellar CELEX/XHTML and inferred-RDF topology surface, already live-validated in GitHub Actions.

Result:

- curated legal/factual provenance: **cleared**;
- current documented Cellar machine route: **cleared for the bounded monitor use**;
- verification mode: `AUTOMATED_PILOT`;
- automatic canonical write remains prohibited.

No source split is needed because the monitored semantic/topology evidence is carried on the documented EUR-Lex/Cellar reuse and machine-access system.

### European Commission / EUR-Lex CBAM — `WSSRC-TRD-005` and `WSSRC-TRD-006`

Primary Commission reuse source: <https://commission.europa.eu/legal-notice_en>  
Primary EUR-Lex machine/reuse source: <https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html?locale=en>

The Commission states that EU-owned website content is generally licensed CC BY 4.0 unless otherwise indicated. The executable CBAM monitors do **not** scrape Commission guidance as their primary legal-state engine: the primary semantic and current-law topology routes are the documented Cellar CELEX/XHTML and inferred-RDF endpoints. Commission CBAM pages are retained as official implementation cross-check/fallback surfaces.

Result for both CBAM source identities:

- curated legal/factual provenance: **cleared**;
- documented primary Cellar machine route: **cleared for the bounded monitor use**;
- verification mode: `AUTOMATED_PILOT`;
- Commission HTML remains a non-primary cross-check rather than silently broadening the automation claim.

No source split is needed: the different EU surfaces have compatible reuse roles and the source records already distinguish primary Cellar endpoints from non-primary Commission cross-checks.

### Colombia — existing composite `WSSRC-REG4-001`

Open Data terms: <https://herramientas.datos.gov.co/terminos>  
SUIN-Juriscol conditions of use: <https://www.suin-juriscol.gov.co/otrosinformacion/Politicayprivacidad.pdf>

The Colombia Open Data Portal states that public data on the portal may be freely used and transformed, including redistribution, compilation, extraction, copying, dissemination, modification and adaptation, for commercial or non-commercial activity, with attribution and preservation of applicable metadata/conditions.

The separate SUIN-Juriscol legal-text portal has a different use regime. Its conditions require correct, lawful and diligent use, source citation and preservation of copyright/rights notices, and expressly prohibit uses that overload, damage or disable the portal or interfere with its normal operation.

The current source identity combines two operationally different jobs:

1. **Datos Abiertos / Socrata inventory** — machine-readable presence/version/status sentinel for typed `DECRETO 111/1996`;
2. **SUIN operative legal text** — authoritative manual clause-level verification of Article 59 after machine evidence indicates a possible change.

The existing monitor architecture already respects this evidentiary distinction: an inventory change is review evidence only and cannot change the derived budget rule until the clause is checked against SUIN.

## Architecture decision — decompose Colombia source identity

One source-level `automated_monitoring_use` value cannot accurately describe both Colombia routes. Assigning a single permissive status would incorrectly project the Open Data terms onto SUIN; assigning one restrictive status would incorrectly hide the permitted machine role of the Open Data dataset.

Therefore:

- retain **`WSSRC-REG4-001`** as the stable canonical legal-authority identity, narrowed to SUIN operative legal text and manual Article 59 verification;
- create **`WSSRC-REG4-002`** for the Colombia Open Data/Socrata legal-instrument inventory machine sentinel;
- keep the stable adapter identity `COLOMBIA_SUIN_DECREE_111_1996`;
- move the adapter's primary `source_id` to `WSSRC-REG4-002`;
- record `WSSRC-REG4-001` explicitly as the required manual authoritative verification source;
- preserve historical audit records that previously referred to the composite `WSSRC-REG4-001` rather than retroactively rewriting them.

This is a source-governance decomposition, **not** a canonical event identity migration. `WSO-REG-D-0001` continues to cite `WSSRC-REG4-001` as its authoritative legal provenance.

## Planned modern classifications

| Source | Canonical provenance | Automated monitoring | Verification mode | Role |
|---|---|---|---|---|
| `WSSRC-FIN-001` | `CLEARED_CURATED_FACTUAL_METADATA` | `ENDPOINT_REVIEW_REQUIRED` | `AUTOMATED_PILOT` | RBA FSR publication monitor |
| `WSSRC-TECH-001` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` | EUR-Lex/Cellar CRA monitor |
| `WSSRC-TRD-005` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` | CBAM verifier/certificate-sale legal monitor |
| `WSSRC-TRD-006` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` | CBAM annual deadline legal monitor |
| `WSSRC-REG4-001` | `MANUAL_INFORMATIONAL_REFERENCE_ONLY` | `ENDPOINT_REVIEW_REQUIRED` | `MANUAL_AUTHORITATIVE_RECHECK` | SUIN operative legal text |
| `WSSRC-REG4-002` | `CLEARED_CURATED_FACTUAL_METADATA` | `CLEARED` | `AUTOMATED_PILOT` | Colombia Open Data/Socrata machine sentinel |

## Transaction boundary

The guarded P0 transaction may change only:

- `data/sources/registry.json`;
- `data/monitor/expectations.json`; and
- `scripts/run_live_monitor.py`.

The canonical registry must remain byte-identical at v0.20 / 669 occurrences. The transaction does not open the canonical auto-commit gate and does not enable Google Calendar writes.
