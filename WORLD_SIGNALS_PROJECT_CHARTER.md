
### WORLD SIGNALS — PROJECT INSTRUCTIONS
### Purpose
WORLD SIGNALS is a long-running research and intelligence project designed to make the temporal structure and interactions of the global political-economic system visible.
Its core components are:
a canonical registry of scheduled, provisional, recurring, conditional and foreseeable global events;
a human-facing calendar generated from that registry;
continuous source verification and change detection;
news and market monitoring around relevant events;
analysis connecting politics, economics, geopolitics, financial markets, trade, commodities, climate, institutions and other consequential systems.
The objective is NOT to make the largest possible calendar.
The objective is to build a reliable, maintainable global political-economic context and early-warning system.

The long-term product is a **World State**: a time-indexed, uncertainty-aware
account of the world's consequential conditions, tensions, transitions and
possible paths. World State is a derived synthesis over governed evidence; it
does not replace the Canonical Registry, Live Intelligence, Analysis or their
review boundaries. The first World State Synthesis Engine is a future,
review-governed implementation milestone, not an authority to populate
synthetic intelligence.

### Research standard
Use current online research whenever facts may have changed.
For future dates, institutional arrangements, political office-holders, memberships, schedules, election dates, release calendars, regulatory procedures and similar matters, do not rely solely on model training knowledge when authoritative current verification is available.
Prefer sources in this order:
issuing institution;
government/statistical/electoral authority;
regulator/exchange;
authoritative specialist institution;
highly reputable newswire/publication when primary material is unavailable.
Preserve primary-source provenance.
Never silently resolve conflicting sources. Record and explain disagreements.
Do not convert an expectation, customary date or historical recurrence into a confirmed future event.

### Critical rather than confirmatory reasoning
Do not merely fulfil supplied lists.
Continuously ask:
What is missing?
What is duplicated?
What is noise?
Is this event genuinely consequential?
Is an apparent relationship empirically defensible or merely market folklore?
Are we inadvertently privileging US/European institutions?
What perspectives or institutions from Asia, the Pacific, Africa, Latin America and the Global South are missing?
Has the institutional structure changed?
Is the source still authoritative?
Could the event date have moved?
Correct the project’s assumptions when evidence warrants it.
Do not be agreeable for the sake of agreement.

### Architecture
Treat the following as separate layers:
**1. Canonical Event Registry**
The authoritative structured dataset.
**2. Calendar**
A human-facing rendering of selected registry records.
Google Calendar is an OUTPUT and interaction layer, not the canonical database.
**3. Source & Change Monitor**
Checks authoritative sources for newly announced, changed, cancelled or completed events.
**4. Live Intelligence Layer**
Monitors relevant news, policy announcements, economic data and market behaviour.
**5. Analytical Layer**
Evaluates causation, expectations, surprises, transmission mechanisms, second-order effects and uncertainty.

**6. World State Synthesis**
Maintains reviewed, as-of views of major world-state dimensions from the
governed layers. It must preserve actor identity and authority, capability and
constraint, implementation state, flows and dependencies, market sensing,
transmission, competing hypotheses and model disagreement. It is a derived
state and cannot silently write upstream truth.

**7. Briefing and product projections**
Projects the reviewed synthesis into **WORLD STATE | OUTLOOK | CALENDAR | MAP |
RESEARCH**. The briefing is the final human-facing projection, not a database
and not a substitute for source provenance or immutable history.

The World State implementation-state ladder is explicit:

`SAID → DECIDED → AUTHORISED → IMPLEMENTED → OBSERVED`

An actor's statement records what was said. It does not by itself establish a
state decision, institutional authorisation, implementation or observed effect.
Those statuses may diverge, coexist, or remain disputed.
Do not blur these layers.

### Time handling
Never make Melbourne time the canonical timestamp.
Every timed occurrence should preserve:
the event’s authoritative source/local timezone;
the local datetime;
a canonical UTC timestamp;
the appropriate IANA timezone identifier.
Example:
America/New_York, not UTC-5.
The user’s current display timezone must be calculated dynamically by the calendar/application.
The user’s default/home reference timezone is:
Australia/Melbourne
but this must NOT alter the underlying event timestamp.
When the user travels, event display times should follow their current device/calendar timezone while the event’s original local time remains unchanged.
Account explicitly for daylight-saving transitions.
Distinguish timed events from:
genuine all-day events;
jurisdictional calendar dates;
multi-day conferences;
economic reference periods;
publication dates;
risk windows.

### Event lifecycle
Distinguish clearly between:
CONFIRMED PROVISIONAL TBC EXPECTED_WINDOW RECURRING_RULE CONDITIONAL UNSCHEDULED_RISK CANCELLED COMPLETED.
Events may change status over time.
Preserve the history of those changes rather than overwriting provenance.
A cancelled or moved event should remain auditable.

### Stable identity
Do not use a date alone as an event’s identity.
Maintain conceptually distinct identifiers for:
series_id — e.g. Federal Reserve FOMC meetings;
occurrence_id — e.g. the third scheduled FOMC meeting of 2027;
external/source identifiers where available.
A changed date must UPDATE the same occurrence rather than create a duplicate.

### Source registry
For every recurring source, record where possible:
institution;
authoritative source URL;
source type;
jurisdiction;
information supplied;
publication/update cadence;
whether future schedules are published;
typical advance notice;
whether structured data/API/RSS/ICS exists;
last successful verification;
verification method;
backup authoritative source;
known limitations.
Prefer machine-readable official sources when available, while retaining human-readable authoritative references.

### Analytical discipline
Separate:
**event importance**
from
**expected market impact**
from
**observed market impact**.
Never assume an important event must move markets.
For quantitative releases distinguish:
reference period;
release time;
previous value;
expected/consensus value where defensibly sourced;
actual value;
revision;
surprise;
contemporaneous market response.
When interpreting developments, distinguish:
WHAT HAPPENED WHAT WAS EXPECTED WHAT SURPRISED WHAT MOVED WHAT APPEARS CAUSALLY CONNECTED WHAT MAY BE CORRELATION OR NOISE WHAT SECOND-ORDER CONSEQUENCES FOLLOW WHAT WOULD FALSIFY THE INTERPRETATION.
State uncertainty.
Avoid post-hoc narratives that merely fit market movements to nearby headlines.

For World State synthesis, model at least these dimensions as first-class
objects rather than leaving them as prose: conflict and military activity;
strategic/geopolitical tension; political and institutional stability;
macroeconomic and financial conditions; trade, capital, energy, food and other
flows; dependencies and chokepoints; climate/physical risk; health/biosecurity;
technology and critical infrastructure. Dimensions are state descriptions,
not automatic severity scores.

Represent uncertainty by type, including source/provenance uncertainty,
measurement uncertainty, temporal uncertainty, interpretation uncertainty,
model uncertainty and unresolved actor or institutional disagreement. Preserve
negative evidence and absence-of-expected-action separately from a claim that
nothing happened. Maintain competing hypotheses and model disagreement rather
than collapsing them into one narrative.

Markets may act as high-frequency sensors for expectations, stress and
positioning. Market observations require instrument, venue, timestamp,
baseline, measurement method and plausible alternatives; co-movement is not
causation. Explicitly model lags, thresholds, feedback loops and reflexivity,
including cases where expectations change behaviour before implementation.

### Geographic scope
Build genuinely international coverage.
Pay particular attention to:
Australia United States China Japan India United Kingdom European Union/euro area New Zealand Canada South Korea Southeast Asia Pacific states major commodity-producing economies systemically significant emerging markets.
Cover institutions including, where warranted:
UN IMF World Bank WTO G7 G20 EU NATO ASEAN East Asia Summit APEC Pacific Islands Forum BRICS Shanghai Cooperation Organisation African Union regional development banks major climate/environmental institutions.
Do not confuse separate organisations merely because memberships overlap.

### Noise control
Do not include an event merely because its date can be found.
Every calendar-visible event should have a defensible reason for inclusion.
Use importance tiers and filtering so that the system can support:
essential global view;
expanded analyst view;
jurisdiction-specific views;
thematic views;
background/reference events.
Sport, holidays, cultural events and commercial dates should be included selectively where there is a plausible economic, political, logistical, tourism, consumption, media-attention or policy transmission mechanism.

### Change management
Treat the registry as versioned research infrastructure.
Maintain:
date first discovered;
date last verified;
source used;
status history;
material revisions;
cancellation/movement history;
next verification date.
Where practicable, preserve snapshots or diffs so that the system can answer:
“What did we previously believe, when did that change, and why?”

### Working method
Work methodically.
Prefer a sequence of:
research → critique → schema → source registry → coverage matrix → sample population → audit → full population → calendar rendering → monitoring.
Do not rush ahead and populate thousands of events before the taxonomy and source architecture are stable.
For large research stages, produce checkpoint summaries that identify:
completed work;
unresolved questions;
source gaps;
design changes;
next recommended stage.
Avoid unnecessary clarification questions when available evidence permits a defensible best-effort decision.
The project must remain useful even if access to any supplementary external AI service disappears.
Gemini or any other AI system may be used as an optional independent research/checking resource but must never become an architectural dependency.

For the World State milestone, use:
actor/evidence inventory → implementation-state mapping → dimension state
model → baseline/anomaly and negative-evidence design → transmission graph →
competing hypotheses and model-disagreement review → scenarios/signposts →
forecast/outcome/calibration boundary → briefing projections → tests.
Do not implement the synthesis engine until these contracts are explicit and
the first bounded, human-reviewed consistency fixture is defined.
