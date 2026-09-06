#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"expected documentation block not found in {path}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


readme = ROOT / "README.md"
replace(readme,
"""Post-#77 / AW controlled Live Intelligence checkpoint:
""",
"""Post-#78 / AX evolving-state Live Intelligence checkpoint:
""")
replace(readme,
"""- Live Intelligence: **v0.2 — 1 reviewed internal observation / 2 primary-official evidence rows; public observation projection closed**
""",
"""- Live Intelligence: **v0.3 — 3 reviewed internal observations / 4 primary-official evidence rows; public observation projection closed**
""")
replace(readme,
"""4. **Live Intelligence** — factual current-development observations; AW v0.2 contains one controlled internal specimen and still exposes zero public observations.
""",
"""4. **Live Intelligence** — factual current-development observations; AX v0.3 contains three controlled internal observations across the Nepal shock and one manually grouped DRC evolving-outbreak story, while still exposing zero public observations.
""")
replace(readme,
"""AW emits `docs/data/live_intelligence.json` as **curated-store metadata only**. The repository contains one reviewed internal observation, but the projection still contains zero public observations and makes no claim to be a current-news or runtime intelligence feed.
""",
"""AX emits `docs/data/live_intelligence.json` as **curated-store metadata only**. The repository contains three reviewed internal observations and four evidence rows, but the projection still contains zero public observations and makes no claim to be a current-news or runtime intelligence feed.
""")
replace(readme,
"""## Live Intelligence controlled population

AV v0.1 established the zero-population contract. AW v0.2 opens it only far enough for one reviewed physical-shock specimen: the 26 August 2026 Bhote Koshi / Rasuwa flood in Nepal.

The controlled state:

- preserves the unscheduled flood without fabricating a Canonical occurrence;
- preserves the authoritative `Asia/Kathmandu` local time `08:40` and matching `02:55Z`;
- keeps WORLD SIGNALS observation time separate from real-world event time;
- adds explicit evidence publication-time precision so civil publication dates cannot be upgraded to invented clock times;
- contains exactly one internal observation and two primary-official evidence rows;
- leaves the uncertain upstream physical trigger unresolved rather than promoting a preliminary mechanism into fact;
- creates no story ID and does not automatically fold the later UN appeal into the shock;
- prohibits causal interpretation, market-move attribution, Analysis-evidence migration and automatic ingestion;
- keeps public observation projection closed at zero.
""",
"""## Live Intelligence controlled population

AV v0.1 established the zero-population contract. AW v0.2 admitted one reviewed Nepal physical-shock specimen. AX v0.3 adds two successive WHO snapshots of the 2026 DRC Bundibugyo outbreak to test evolving-state semantics without opening broad ingestion.

The controlled state:

- preserves the Nepal shock unchanged, without fabricating a Canonical occurrence;
- preserves the authoritative Nepal `Asia/Kathmandu` local time `08:40` and matching `02:55Z`;
- adds two DRC `HEALTH_EMERGENCY` observations sharing one manually reviewed story key;
- preserves the 26 August and 30 August DRC epidemiological states as separate observations rather than silently overwriting the earlier snapshot;
- keeps `state_update_of_observation_id` distinct from `revision_of_observation_id`: later state is not automatically a correction of earlier history;
- separates state-as-of time, evidence publication time, event time and WORLD SIGNALS observation time, preserving civil-date precision where that is all the source supplies;
- treats the story key only as a reviewed grouping identity, never as a Canonical event, causal claim or analytical conclusion;
- prohibits automatic story clustering, causal interpretation, market-move attribution, Analysis-evidence migration and automatic ingestion;
- contains exactly three internal observations and four primary-official evidence rows;
- keeps public observation projection closed at zero.

Any fourth observation, continuous outbreak ingestion or broader Live population requires another pressure audit.
""")

status = ROOT / "PROJECT_STATUS.md"
replace(status,
"""# CURRENT RECOVERY OVERRIDE — POST-AV / AW CONTROLLED LIVE INTELLIGENCE

**Effective checkpoint:** 2026-09-06
**Exact post-#77 main base:** `4768c73532c4ba4038b30314079b85be64fbee01`
**AW branch:** `feature/post-av-pressure-audit-aw`
""",
"""# CURRENT RECOVERY OVERRIDE — POST-AW / AX EVOLVING-STATE LIVE INTELLIGENCE

**Effective checkpoint:** 2026-09-06
**Exact post-#78 main base:** `721206169033eb0ceb695075d44fb38e7fa2edc3`
**AX branch:** `feature/post-aw-pressure-audit-ax`
""")
replace(status,
"""- Live Intelligence: **v0.2 / 1 reviewed internal observation / 2 primary-official evidence rows / public observation projection CLOSED**
""",
"""- Live Intelligence: **v0.3 / 3 reviewed internal observations / 4 primary-official evidence rows / public observation projection CLOSED**
""")
replace(status,
"""## Current architecture decision

AW has exercised the Live Intelligence contract with its first real specimen without opening a general feed. Live Intelligence v0.2 contains one internally curated physical-shock observation for the 26 August 2026 Nepal Bhote Koshi / Rasuwa flood and exactly two primary-official evidence rows. Public observation projection, automatic ingestion, story clustering, automatic Canonical commit and Google Calendar writes remain closed.

The specimen has no fabricated Canonical occurrence or link. Native `Asia/Kathmandu` event time is preserved as `2026-08-26T08:40:00` / `2026-08-26T02:55:00Z`; evidence publication dates remain civil-date precision; the uncertain upstream physical trigger is deliberately not asserted as cause.

The next pressure audit should determine whether Live Intelligence now needs repeated as-of state / revision / developing-story semantics before prospective Live Intelligence → Analysis linkage. The 2026 DRC Bundibugyo Ebola outbreak is a strong candidate but is not pre-authorised. Japan household spending remains a valid held Analysis specimen, not a queue-completion obligation.
""",
"""## Current architecture decision

AX has now exercised repeated as-of state and developing-story semantics without opening a general feed. Live Intelligence v0.3 preserves the AW Nepal shock and adds two primary-confirmed WHO snapshots of the 2026 DRC Bundibugyo outbreak, giving three internal observations and four primary-official evidence rows in total.

The two DRC observations share one manually reviewed story key. The 30 August snapshot explicitly state-updates the 26 August snapshot while both retain `revision_of_observation_id = null`: a later cumulative state does not make the earlier as-of state false. `state_as_of` is separate from source publication time, event time and WORLD SIGNALS observation time, and civil dates are not upgraded to fabricated timestamps.

Public observation projection, automatic ingestion, automatic story clustering, automatic Canonical commit and Google Calendar writes remain closed. The DRC story key is not a Canonical occurrence, causal claim or analytical conclusion. A fourth observation or broader ingestion requires another pressure audit.

The next audit should decide whether prospective Live Intelligence → Analysis linkage now creates more architectural value than another isolated Live specimen. Japan household spending remains a valid held Analysis specimen, not a queue-completion obligation.
""")

architecture = ROOT / "ARCHITECTURE.md"
replace(architecture,
"""Current post-#77 / AW controlled Live Intelligence state:
""",
"""Current post-#78 / AX evolving-state Live Intelligence state:
""")
replace(architecture,
"""- Live Intelligence `v0.2 / 1 internal observation / 2 evidence`, controlled single-specimen gate; public observations `0`;
""",
"""- Live Intelligence `v0.3 / 3 internal observations / 4 evidence`, controlled multi-snapshot gate; public observations `0`;
""")
replace(architecture,
"""AV introduced the executable Live Intelligence contract at `data/live_intelligence/`; AW v0.2 admits the first reviewed internal specimen without opening broad ingestion.
""",
"""AV introduced the executable Live Intelligence contract at `data/live_intelligence/`; AW v0.2 admitted the first reviewed internal specimen, and AX v0.3 adds a bounded evolving-state story test without opening broad ingestion.
""")
replace(architecture,
"""The frozen AV v0.1 checkpoint remains recorded inside the v0.2 schema. AW opens production only under `CONTROLLED_SINGLE_SPECIMEN`: maximum one observation and two evidence rows, automatic ingestion disabled, story clustering disabled and public observation projection closed.
""",
"""The frozen AV v0.1 and AW v0.2 checkpoints remain recorded inside the v0.3 schema. AX uses `CONTROLLED_MULTI_SNAPSHOT_SPECIMEN`: maximum three observations and four evidence rows, automatic ingestion disabled, automatic story clustering disabled and public observation projection closed. The DRC observations demonstrate that a later state snapshot is not automatically a correction of the earlier snapshot, and that a manual story key is only a grouping identity.
""")
replace(architecture,
"""Likewise, AW emits `docs/data/live_intelligence.json` only as **curated-store metadata**. It reports one internal observation and two internal evidence rows while exposing zero public observations and explicitly stating that it is not a runtime feed. A browser Live Intelligence feed is not authorised by this tranche.
""",
"""Likewise, AX emits `docs/data/live_intelligence.json` only as **curated-store metadata**. It reports three internal observations and four internal evidence rows while exposing zero public observations and explicitly stating that it is not a runtime feed. A browser Live Intelligence feed is not authorised by this tranche.
""")
replace(architecture,
"""  -> first pressure-audited Live Intelligence specimen       [DONE: AW — Nepal flood]
  -> test prospective Live Intelligence -> Analysis linkage  [LATER, IF CONTRACT SURVIVES]
""",
"""  -> first pressure-audited Live Intelligence specimen       [DONE: AW — Nepal flood]
  -> evolving-state / manual story semantics                  [DONE: AX — DRC Bundibugyo]
  -> test prospective Live Intelligence -> Analysis linkage  [NEXT AUDIT CANDIDATE]
""")

roadmap = ROOT / "ROADMAP.md"
replace(roadmap,
"""**AV v0.1 deliberately prohibited production observation/evidence population; that frozen foundation checkpoint is preserved inside AW v0.2.**
""",
"""**AV v0.1 deliberately prohibited production observation/evidence population; that frozen foundation checkpoint remains preserved through AW v0.2 and AX v0.3.**
""")
replace(roadmap,
"""## Stage 7 — first Live Intelligence specimen — DONE / AW

AW selected the 26 August 2026 Bhote Koshi / Rasuwa flood in Nepal after comparing physical-shock, health-emergency, geopolitical/policy, economic-revision and market-observation candidates. Selection was based on contract pressure and authoritative provenance rather than headline prominence.

Live Intelligence v0.2 now contains exactly one reviewed internal `PHYSICAL_SHOCK` observation and two primary-official evidence rows. It preserves `Asia/Kathmandu` native time, permits zero Canonical links for a genuinely unscheduled shock, enforces civil-date publication precision for evidence, leaves the uncertain upstream trigger unresolved, creates no story identity and exposes zero public observations.

The next pressure audit should decide whether repeated as-of state / revision / developing-story semantics now outrank prospective Live Intelligence → Analysis linkage. The 2026 DRC Bundibugyo Ebola outbreak is a strong candidate for that stress test, but is not pre-authorised for population.
""",
"""## Stage 7 — controlled Live Intelligence specimens — DONE / AW + AX

AW selected the 26 August 2026 Bhote Koshi / Rasuwa flood in Nepal after comparing physical-shock, health-emergency, geopolitical/policy, economic-revision and market-observation candidates. Live Intelligence v0.2 proved unscheduled identity, native event time, civil-date publication precision and zero Canonical links without opening public projection.

AX then selected the 2026 DRC Bundibugyo outbreak because successive WHO snapshots stress a different contract boundary: **state evolution is not revision**. Live Intelligence v0.3 preserves the Nepal row and adds two DRC `HEALTH_EMERGENCY` observations sharing one manually reviewed story key. The 30 August state points to the 26 August state with `state_update_of_observation_id`, while both retain null revision links.

AX also makes state-as-of time explicit and distinct from event, publication and WORLD SIGNALS observation time. Manual story identity is a grouping key only; automatic clustering, public projection and continuous ingestion remain closed. Current bounded population is three observations and four primary-official evidence rows.

Before any fourth observation, run another pressure audit. The next high-value candidate is prospective Live Intelligence → Analysis linkage rather than automatic continuation of the DRC story.
""")

# Executable-state cross-check.
schema = json.loads((ROOT / "data/live_intelligence/schema.json").read_text(encoding="utf-8"))
obs = json.loads((ROOT / "data/live_intelligence/observations.json").read_text(encoding="utf-8"))
ev = json.loads((ROOT / "data/live_intelligence/evidence_registry.json").read_text(encoding="utf-8"))
assert schema["version"] == "0.3"
assert len(obs["observations"]) == 3
assert len(ev["evidence"]) == 4
assert obs["population_state"] == "CONTROLLED_MULTI_SNAPSHOT_SPECIMEN"
print("AX current documentation refresh PASS")
