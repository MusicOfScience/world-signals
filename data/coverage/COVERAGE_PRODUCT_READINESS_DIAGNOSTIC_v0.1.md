# WORLD SIGNALS — coverage + product-readiness diagnostic v0.1

**Reference date:** 2026-09-05  
**Verified main:** `46da3307fe2a54fb4a755e58bd77ec6edb900967`  
**Canonical registry:** v0.26 / 669 occurrences  
**Source registry:** v1.67 / 228 sources  
**Change ledger:** v0.15  
**Fresh mechanical evidence:** Actions run `33956008699`, conclusion `SUCCESS`, head SHA exactly verified main  
**Canonical mutation authorised by this diagnostic:** **NO**

## Executive finding

The post-#39 architecture is mature enough to stop treating source-governance backfill as the product. The next useful unit of work is a paired correction:

1. keep selecting new canonical series only when they add genuinely missing signal systems; and
2. expose the existing registry through a human-first short-horizon surface.

The current registry is not simply “too small”. It is uneven in ways that occurrence counts can obscure.

- Monetary policy + macro releases are **437 / 669 occurrences (65.3%)**.
- South Asia remains the only mechanically thin region at **7 series / 5 institutions**, and its occurrence count is still dominated by Indian macro releases.
- Africa (**10 series / 10 institutions**) and Southeast Asia (**10 / 10**) are lower-count but already institutionally diverse; quota-filling either region would be a mistake.
- `PHYSICAL_CLIMATE_RISK` remains structurally narrow at **3 series / 3 institutions**.
- `HEALTH_BIOSECURITY` remains **5 series / 1 institution**, but the concentration partly reflects correct taxonomy: animal health, plant health and biological arms control should not be forced into WHO-style human-health governance.
- `ENERGY_COMMODITIES` is materially broader than the early audit but remains frequency-heavy relative to distinct institutions.

## Current web diagnosis

The current page already gets several hard things right:

- the browser is a read-only projection, not canonical state;
- source-native timezone is retained while timed events can display in device-local time;
- exact-date calendar events and uncertain/month-precision windows are rendered separately;
- intrinsic importance, expected market sensitivity and authoritative source URL are already present in the public projection;
- source/change monitoring, retained operational evidence and reviewed change history remain separate layers.

The main product problem is therefore not missing machinery. It is **entry-point orientation**.

A user currently arrives at an engineering-labelled “executable thin slice” whose primary tool view is a monthly calendar. That is useful for inspection but weak for the ordinary WORLD SIGNALS question:

> What matters now, over the next week, and over the next month?

### First useful surface

Add a derived read-only Horizon surface before the tool views:

- **NOW** — exact events active on the device-local current date;
- **NEXT 7 DAYS** — exact events beginning tomorrow through day 7;
- **NEXT 30 DAYS** — exact events beginning on days 8–30, so rows are not repeated;
- **WINDOWS IN VIEW** — expected/date ranges and month-bounded seasonal windows overlapping the next 30 days, kept separate so no exact day is manufactured.

The Horizon reads only:

- `docs/data/events.json`, derived from the canonical registry/source registry; and
- `docs/data/changes.json`, the reviewed canonical change ledger.

It is not a Live Intelligence surface and must not infer current news, market response, source health or causal interpretation.

### User-facing filters

The Horizon should translate canonical categories into a small product vocabulary without altering the underlying taxonomy:

- Economics / central banks / fiscal / markets
- Elections / politics
- Geopolitics / institutions
- Trade / sanctions
- Commodities / energy / food
- Climate / physical risk
- Technology / infrastructure
- Health / biosecurity
- Region
- Jurisdiction

Each visible event should expose, without requiring the user to understand repository internals:

- what it is;
- device-local time where a canonical UTC instant exists;
- preserved source/native timezone;
- certainty;
- intrinsic importance;
- expected market sensitivity;
- authoritative source;
- a compact reviewed-change marker where that occurrence changed within the last 30 days.

No value should be inferred when the registry says `UNRATED_PENDING_CALIBRATION`.

## Candidate tranche review

This pass rechecked earlier held candidates against the current registry and current first-party sources. The point is not to force a population count; it is to identify which candidates now clear the gate and which still do not.

### A. Central Bank of Nigeria MPC — `ADD_NEXT_MIXED_TRANCHE`

**Why it matters:** Nigeria is systemically important in African monetary, FX, oil/fiscal and regional financial conditions. The existing registry has Nigerian elections but no CBN monetary-policy series.

**Current primary evidence:**  
`https://www.cbn.gov.ng/MonetaryPolicy/calendar.html`

The CBN now publishes a first-party **MPC Meeting Calendar for 2026**, including:

- meeting 307: **21–22 September 2026**
- meeting 308: **23–24 November 2026**

This materially changes the earlier research outcome, which had found only a decision-history page and therefore held CBN as “monitor until dated”.

**Canonical shape:** one stable `MONETARY_POLICY_MEETING_WINDOW` series, two exact two-day civil-date occurrences. Do not invent a decision-release clock time from meeting convention.

**Disposition:** clears factual scheduling and ontology gates. Do **not** add it as a one-series standalone correction merely to raise Africa counts; carry it into the next mixed population tranche.

### B. BWC Working Group on strengthening the Convention — `READY_AFTER_CATEGORY_FREEZE`

**Why it matters:** biological-security governance is consequential for geopolitical risk, dual-use technology, treaty compliance and preparedness, while currently absent as a canonical series.

**Primary evidence:**  
`https://meetings.unoda.org/bwc-/biological-weapons-convention-working-group-on-the-strengthening-of-the-convention-tenth-session-2026`

UNODA confirms the tenth session in Geneva on **7–11 December 2026**, with daily sessions 10:00–13:00 and 15:00–18:00.

**Canonical shape:** one multi-day treaty-working-group occurrence. The meeting belongs naturally under international/security governance, with biosecurity represented through the existing cross-domain overlay rather than by misclassifying it as human `HEALTH_BIOSECURITY`.

**Disposition:** timing and authority clear. Freeze canonical category/subcategory placement before mutation.

### C. WOAH 94th General Session / World Assembly of Delegates — `READY_AFTER_CATEGORY_FREEZE`

**Why it matters:** the World Assembly adopts international animal-health standards and governance decisions with direct implications for zoonotic risk, livestock trade and One Health.

**Primary current HTML evidence:**  
`https://rr-africa.woah.org/en/news/woah-93rd-general-session-its-relevance-for-africa/`

WOAH states the 94th General Session will run **24–28 May 2027** in Paris.

**Canonical shape:** one multi-day governance assembly occurrence. It should remain in its natural international-institutions / animal-health-trade domain and appear in the biosecurity overlay; it must not be imported into the human-health category simply to change an institution count.

**Disposition:** exact timing now established; freeze primary category/subcategory and conservative source-governance state before population.

### D. IPPC Commission on Phytosanitary Measures CPM-21 — `HOLD_SOURCE_STATUS_CONFLICT`

The 2027 IPPC calendar gives **5–9 April 2027** at FAO Headquarters, Rome. However current official language surfaces are inconsistent about whether CPM-21 itself is explicitly marked tentative:

- one official calendar rendering lists the dates without a tentative marker on that row;
- another official language rendering labels it **“Tentative: CPM-21”**.

The date range is therefore not the problem; certainty semantics are.

**Disposition:** do not silently select one official surface. Hold until the authoritative status is reconciled or populate only under an explicitly conservative provisional rule after review.

### E. North Indian Ocean cyclone season — `HOLD_OFFICIAL_DEFINITION_CONFLICT`

The month/multi-phase timing ontology is now technically capable of representing the candidate without invented civil-day endpoints. The blocker is no longer schema capability.

The blocker is first-party semantic conflict inside IMD/RSMC New Delhi material:

- the Pre-Cyclone Exercise document says two cyclone seasons: **April–June** and **October–December**;
- the official terminology document defines “Storm season” as **April–May** and **October–December**.

**Disposition:** remain noncanonical. Do not pick the broader first phase merely because it would repair South Asia and physical-risk counts simultaneously.

### F. South Asia non-monetary candidates — `CONTINUE_MONITOR_HOLDS`

The prior South Asia depth findings remain materially intact:

- Nepal federal budget: strong native-calendar legal boundary, but authoritative Gregorian conversion provenance remains unresolved;
- Bangladesh federal budget: active official preparation process, no exact future presentation date;
- BIMSTEC: strategically useful, insufficiently precise forward high-level timing;
- Bangladesh Bank MPS: recurring publication pattern but no exact future release date that should be promoted.

This is evidence of a **real** regional depth gap, but not evidence that another South Asian canonical row should be manufactured now.

## Bounded population tranche to prepare next

Freeze the next mixed tranche around **three distinct signal systems / four occurrences**, subject to final taxonomy and source-governance simulation:

1. **Central Bank of Nigeria MPC meeting windows** — 2 occurrences — Africa / monetary policy
2. **BWC Working Group, tenth session** — 1 occurrence — global / security-institutions / biosecurity overlay
3. **WOAH 94th General Session** — 1 occurrence — global / animal-health standards / biosecurity overlay

This tranche is intentionally small. It adds:

- one important African monetary institution;
- one missing biological-security treaty process;
- one missing animal-health standards/governance institution;

without pretending that South Asia's unresolved source problems are solved and without filling Africa or health categories by quota.

### Preconditions before canonical mutation

- reconcile exact canonical/category/subcategory identities against the full current registry;
- freeze stable series and occurrence IDs;
- add or reuse first-order source records;
- classify factual provenance separately from automated-retrieval permission;
- preserve source-native date precision and meeting-window semantics;
- run fail-closed in-memory simulation against exact `v0.26 / 669` and source `v1.67 / 228`;
- re-run validator, full tests, Python/JS/site build and coverage audit;
- remove all transaction-only helpers/workflows before PR review.

## Decision for this PR

Proceed with the **Horizon product surface + this durable current diagnostic**.

Do **not** mutate canonical/source registries in the same change. The mixed tranche is now bounded enough to research and simulate next, but two of its three series still need an explicit category/source-governance freeze. Combining that mutation with the first user-facing surface would make review less legible and would blur a useful boundary between product projection and canonical population.

Safety remains unchanged:

- automatic canonical commit: **OFF**
- Google Calendar writes: **OFF**
- browser canonical write: **impossible**
