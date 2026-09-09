from __future__ import annotations

import json
from pathlib import Path
from urllib import robotparser

from world_signals.adapters.nhc_atlantic_season import (
    NHC_ATLANTIC_BASIN_RSS_URL,
    NHC_ATLANTIC_OUTLOOK_RSS_URL,
    NHC_CLIMATOLOGY_URL,
    NHC_ROBOTS_URL,
    NHC_RSS_DIRECTORY_URL,
    fetch_nhc_atlantic_climatology,
    fetch_nhc_atlantic_outlook_health,
)
from world_signals.adapters.base import USER_AGENT
from world_signals.nhc_atlantic_season_monitor import nhc_atlantic_season_review_candidates


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "monitor" / "NHC_ATLANTIC_SEASON_CF_READINESS_v0.1.json"
TARGET_IDS = ["WSO-COM-A-0049", "WSO-COM-A-0050"]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    canonical = load(ROOT / "data" / "canonical" / "registry.json")
    definition, climo_snapshot = fetch_nhc_atlantic_climatology()
    rss_snapshot = fetch_nhc_atlantic_outlook_health()

    robots = robotparser.RobotFileParser()
    robots.set_url(NHC_ROBOTS_URL)
    robots.read()
    paths = {
        "climatology": NHC_CLIMATOLOGY_URL,
        "rss_directory": NHC_RSS_DIRECTORY_URL,
        "atlantic_outlook_rss": NHC_ATLANTIC_OUTLOOK_RSS_URL,
        "atlantic_basin_rss": NHC_ATLANTIC_BASIN_RSS_URL,
    }
    allowed = {name: robots.can_fetch(USER_AGENT, url) for name, url in paths.items()}
    if not all(allowed.values()):
        raise SystemExit(f"NHC readiness blocked by crawler policy: {allowed}")

    config = {
        "source_id": "WSSRC-RISK-002",
        "canonical_occurrence_ids": TARGET_IDS,
        "schedule_authority": False,
        "lifecycle_authority": False,
        "certainty_authority": False,
        "automatic_new_occurrence_creation_allowed": False,
        "automatic_live_or_analysis_promotion_allowed": False,
        "automatic_commit_allowed": False,
    }
    candidates, observations = nhc_atlantic_season_review_candidates(
        canonical["records"], definition, config
    )
    if candidates:
        raise SystemExit(f"NHC live readiness detected semantic drift; activation blocked: {candidates}")
    if (definition.start_month_day, definition.end_month_day) != ("06-01", "11-30"):
        raise SystemExit("NHC current live definition differs from reviewed CF baseline")

    result = {
        "project": "WORLD SIGNALS",
        "dataset": "NHC_ATLANTIC_SEASON_CF_READINESS",
        "version": "0.1",
        "source_id": "WSSRC-RISK-002",
        "canonical_occurrence_ids": TARGET_IDS,
        "definition": definition.as_dict(),
        "climatology_snapshot": climo_snapshot.as_dict(),
        "atlantic_outlook_rss_snapshot": rss_snapshot.as_dict(),
        "robots_path_access": allowed,
        "review_candidate_count": 0,
        "observation_count": len(observations),
        "semantic_baseline_match_count": len([x for x in observations if x.get("semantic_match") is True]),
        "rss_is_schedule_authority": False,
        "automatic_canonical_commit": False,
        "automatic_live_or_analysis_promotion": False,
        "readiness_verdict": "PILOT_ROUTE_VALIDATED_NO_AUTO_COMMIT",
        "opec_quarantine_respected": True,
        "remote_source_body_retained": False,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
