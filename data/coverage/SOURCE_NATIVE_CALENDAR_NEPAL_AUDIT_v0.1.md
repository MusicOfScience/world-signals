# WORLD SIGNALS — Nepal source-native calendar admission audit v0.1

**Review date:** 2026-09-05  
**Base main:** `49a9d7920c2b5e33f94ce14e7684b6dc63263caa`  
**Base canonical registry:** v0.27 / 673  
**Base source registry:** v1.68 / 231  
**Base canonical schema:** v0.51  
**Canonical mutation authorised by this research document alone:** **NO**

## Finding

Nepal's federal budget exposes a general internationalisation defect in WORLD SIGNALS rather than a missing-date research failure.

The competent legal framework fixes the annual federal budget presentation on **15 Jestha**. For the next budget cycle the authoritative canonical date is therefore **15 Jestha 2084 (Bikram Sambat)**. As at this review, no competent Nepal-government source has been found that supplies the corresponding Gregorian civil date for 2084. WORLD SIGNALS must not substitute a third-party Bikram Sambat converter or infer a Gregorian day from prior years.

The correct representation is consequently:

- the occurrence is canonically **CONFIRMED** in the source-native calendar;
- its Gregorian projection remains explicitly **UNRESOLVED_AUTHORITATIVE_CONVERSION**;
- Gregorian fields remain null;
- the Calendar and NOW/NEXT Horizon do not place it on a Gregorian day;
- a separate read-only SOURCE-NATIVE DATES surface exposes the exact competent-jurisdiction date;
- coverage audits count the canonical series while separately reporting that it is not Gregorian-schedulable.

This separates event certainty from projection/conversion readiness.

## Authoritative evidence

### Legal authority — Nepal Law Commission

Current Constitution landing page:  
https://lawcommission.gov.np/content/13437/nepal-s-constitution/

Official Law Commission repository text/PDF contains Constitution of Nepal Article 119. Article 119(3) states that the Finance Minister must present the revenue and expenditure estimates to the Federal Parliament **on the fifteenth day of Jestha every year**.

Canonical role: legal recurring-rule authority.

### Current budget occurrence / publication corroboration — Ministry of Finance

Current FY 2083/84 budget statement:  
https://mof.gov.np/content/1741/budget-statement-for-the-financial-year-2083-84/

Budget speech archive:  
https://mof.gov.np/category/budget-speech/

The current FY 2083/84 statement is published as **15 Jestha 2083**; the archive also preserves prior budget-speech material. This corroborates the budget-process object and source-native dating practice, but historical publication rows are **not** used to manufacture the future 2084 Gregorian conversion.

Canonical role: current budget/publication corroboration and future manual schedule verification.

## Why the old hold is no longer the right model

The earlier South Asia depth audit correctly refused to populate Nepal because the existing timing model implicitly required a Gregorian civil date before admission. That protected the registry from a third-party conversion, but it also conflated two separate questions:

1. **Is the event date known authoritatively?** — yes, 15 Jestha annually.
2. **Can WORLD SIGNALS authoritatively express that date in Gregorian form yet?** — no for 2084.

Treating the entire occurrence as `TBC` would now discard genuine authoritative precision. Treating it as a Gregorian date would invent precision. `SOURCE_NATIVE_CALENDAR_DATE` preserves both truths.

## Canonical shape

Series: `WSER-FIS-NP-FEDERAL-BUDGET`  
Occurrence: `WSO-FIS-NP-BUDGET-2084`

Classification:

- category: `FISCAL_SOVEREIGN_FINANCE`
- subcategory: `national_budget`
- event_type: `FISCAL_POLICY_PROCESS`
- jurisdiction: `Nepal`
- region: `South Asia`
- institution: `Ministry of Finance, Government of Nepal`
- activation: `AUTHORITATIVE_RECURRING_RULE`
- certainty: `CONFIRMED`
- lifecycle: `PLANNED`
- visibility: `ANALYST`
- intrinsic importance: `HIGH`
- expected market sensitivity: `MEDIUM`

Timing:

- `timing_type = SOURCE_NATIVE_CALENDAR_DATE`
- `native_calendar_system = BIKRAM_SAMBAT_NEPAL`
- `native_calendar_year = 2084`
- `native_calendar_month = JESTHA`
- `native_calendar_day = 15`
- `source_native_date_label = 15 Jestha 2084`
- `gregorian_resolution_status = UNRESOLVED_AUTHORITATIVE_CONVERSION`
- `publication_time_semantics = SOURCE_NATIVE_DATE_ONLY`
- `time_precision = DAY`
- all Gregorian/local/UTC/date-window fields remain null.

The occurrence is a fixed presentation occurrence, not a `BUDGET_SUBMISSION_DEADLINE`. The constitutional text says the estimates are to be presented **on** the date.

## Source governance

Create two first-order sources:

- `WSSRC-FIS-026` — Nepal Law Commission Constitution / Article 119 legal authority;
- `WSSRC-FIS-027` — Nepal Ministry of Finance budget-statement/archive surface.

No general unrestricted production-crawling licence was established in this review. Both therefore remain conservative manual authoritative provenance routes. Public accessibility and official status do not create automated-monitoring permission.

The legal source is not replaced by the Ministry publication archive, and the Ministry archive is not promoted into a legal conversion authority.

## Schema rule

Add a reusable timing object rather than a Nepal exception:

> An authoritative source-native civil-calendar date may be canonical before an authoritative Gregorian mapping exists. Preserve the native calendar components; keep Gregorian timing fields empty until a competent mapping is available. Event certainty and Gregorian-resolution status are independent.

When a competent source later publishes the 2084 Gregorian mapping, update the **same occurrence identity**, preserve the native date and status history, and move the Gregorian projection to the appropriate civil-date timing semantics. Do not create a duplicate occurrence.

## Coverage interpretation

Admission would add one distinct South Asia fiscal series and one Nepal institution/source family. That is useful because South Asia is currently thin and India-macro concentrated, but it is not quota filling: the series is admitted because the legal event itself is authoritatively defined and systemically relevant.

The coverage audit must separately report unresolved source-native dates so canonical breadth is never confused with Gregorian calendar readiness.

## Physical-risk finding retained

This work does **not** populate the North Indian Ocean cyclone season. The architecture can represent multi-phase month windows, but reviewed IMD/RSMC New Delhi first-party materials still conflict over the source-defined season boundary. The object remains held rather than being selected to repair both South Asia and `PHYSICAL_CLIMATE_RISK` counts at once.

## Safety

- automatic canonical commit remains **OFF**;
- Google Calendar writes remain **OFF**;
- no live monitor route is activated by this design;
- no third-party calendar converter becomes a dependency;
- no Gregorian date is inferred from historical practice.
