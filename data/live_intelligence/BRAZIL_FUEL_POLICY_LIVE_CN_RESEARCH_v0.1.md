# WORLD SIGNALS — Brazil fuel-policy Live research CN v0.1

**Status:** REVIEWED RESEARCH / BOUNDED LIVE CANDIDATE  
**Reference date:** 2026-09-10  
**Exact post-CM base main:** `9386114de527b117987058cb1b9cd98066dab8e4`  
**Selection source:** `data/coverage/POST_CM_PRESSURE_AUDIT_CN_v0.1.md`

## Decision

Proceed with one bounded `LIVE_INTELLIGENCE` observation describing the Brazilian Federal Government's first-party announcement that it adopted/signed a temporary fuel-price policy package on 9 September 2026.

The Live claim is intentionally narrower than a legal-effect claim. CN does **not** assert that the newly announced substantive decree and measure provisional had already been published in the Diário Oficial or entered into force at the time of the fresh CN recheck.

## Primary factual source

Ministério da Fazenda:

- title: `Governo Federal adota novas medidas para combustíveis após novos aumentos do petróleo`;
- URL: `https://www.gov.br/fazenda/pt-br/assuntos/noticias/2026/setembro/governo-federal-adota-novas-medidas-para-combustiveis-apos-novos-aumentos-do-petroleo/`;
- page displays `Publicado em 09/09/2026 18h47`;
- the reviewed page does not itself state an IANA timezone for that displayed clock time, so CN preserves source publication precision only as `CIVIL_DATE` `2026-09-09`;
- the article says the Federal Government adopted two measures on 9 September in response to persistent international oil-price volatility and fuel-supply restrictions which the government associates with geopolitical conflicts;
- it says a signed decree reduces PIS/Pasep and Cofins on gasoline by R$0.63/litre and zeroes those contributions on hydrated ethanol for the stated 10 September–9 October period;
- it says a signed measure provisional authorises an economic subsidy for road diesel, initially R$1.00/litre, adjustable by a Ministry of Finance act;
- it describes the measures as temporary cushioning against the external fuel/oil shock.

CN uses this source as reviewed factual evidence only. Public accessibility does not create unattended-monitoring permission or Source Registry authority.

## Fresh legal-status recheck

Rechecked after #121 merged, at approximately `2026-09-10T03:34:45-03:00` (`America/Sao_Paulo`) / `2026-09-10T06:34:45Z`.

### Presidency / Planalto — measure-provisional index

`https://www.planalto.gov.br/ccivil_03/mpv/quadro/_quadro2023-2026.htm`

At the recheck, the indexed list topped out at:

- MP 1.390, dated 8 September 2026, published in the DOU on 9 September; and
- MP 1.389, dated 8 September 2026, published in the DOU on 9 September.

No newly indexed 9 September substantive diesel-policy MP corresponding cleanly to the Finance Ministry announcement was retrieved in the reviewed search.

### Presidency / Planalto — decree index

`https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/_decretos2026.htm`

At the recheck, the indexed list topped out at decrees dated 8 September 2026, including Decree 13.115. No newly indexed 9 September gasoline/ethanol decree corresponding cleanly to the Finance Ministry announcement was retrieved in the reviewed search.

### Related extraordinary-credit measure — context only

MP 1.389 of 8 September 2026:

`https://planalto.gov.br/ccivil_03/_ato2023-2026/2026/mpv/mpv1389.htm`

This opens R$6.605 billion in extraordinary credit for the Ministry of Mines and Energy, including appropriations tied to pre-existing fuel-subsidy measures MP 1.358/2026 and MP 1.363/2026. CN does **not** treat MP 1.389 as the newly announced 9 September substantive policy pair.

## Identity search

Fresh repository search did not identify an existing Live observation representing this 9 September Brazil fuel-policy intervention. CN therefore adds one new Live identity rather than revising an existing row.

No Canonical occurrence is created. The development is an unscheduled policy intervention and the Live schema explicitly permits an unscheduled observation with zero Canonical links.

## Time contract

- real-world policy-adoption/signing date: `2026-09-09` at `CIVIL_DATE` precision;
- no signing clock time is invented;
- source publication: `2026-09-09` at `CIVIL_DATE` precision;
- the page's displayed `18h47` is not converted to UTC because the reviewed page does not itself establish the source timezone;
- WORLD SIGNALS observation time is separate and may be stored as an exact UTC timestamp.

## Live semantic boundary

CN may state that the Brazilian government says it adopted/signed the package and may report the parameters attributed to the Finance Ministry announcement.

CN may **not** state or imply without separate evidence that:

- the newly announced substantive decree/MP pair had already been published in the DOU at CN recheck time;
- the new instruments were already legally in force;
- a particular legal instrument number belongs to the 9 September package;
- domestic pump prices fell;
- inflation fell or was prevented from rising by a quantified amount;
- supply conditions improved;
- any market move was caused by the announcement;
- geopolitical conflict independently caused a quantified Brazilian outcome merely because the government framed the package in that context.

The geopolitical wording remains explicitly attributed to the government source and is not converted into WORLD SIGNALS causal analysis.

## Proposed bounded specimen

- observation id: `WSLI-POL-BRA-FUEL-POLICY-20260909-001`;
- observation type: `POLICY_DEVELOPMENT`;
- verification state: `PRIMARY_CONFIRMED`;
- jurisdiction: `Brazil`;
- region: `Latin America`;
- domain tags: `ECONOMICS`, `COMMODITIES`, `GEOPOLITICS`;
- Canonical links: none;
- evidence rows: exactly one primary-official Finance Ministry row;
- event time: `CIVIL_DATE` `2026-09-09`;
- publication time: `CIVIL_DATE` `2026-09-09`;
- no Analysis population;
- no Monitor route;
- no Source Registry mutation;
- no Canonical mutation;
- no Calendar write;
- no public Live projection.

## Versioning

CN is a controlled population expansion after CM v0.9. The proposed target is Live **v0.10**, 9 observations and 12 evidence rows. CM's correction/conflict contract remains intact and is not weakened or reinterpreted.

## Abort / revise rule

If, before materialisation, fresh official evidence shows that the package was corrected, withdrawn, materially altered, superseded, or that the source no longer supports the bounded claim above, CN must revise or abort rather than force the selected specimen.
