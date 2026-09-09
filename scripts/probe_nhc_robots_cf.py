from __future__ import annotations

import json
from pathlib import Path
from urllib import robotparser


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "monitor" / "NHC_ATLANTIC_SEASON_CF_ROBOTS_PROBE_v0.1.json"
ROBOTS = "https://www.nhc.noaa.gov/robots.txt"
USER_AGENT = "WORLD-SIGNALS/0.2 (+https://github.com/MusicOfScience/world-signals)"
TARGETS = {
    "climatology": "https://www.nhc.noaa.gov/climo/",
    "rss_directory": "https://www.nhc.noaa.gov/mobile/rss.html",
    "atlantic_outlook_rss": "https://www.nhc.noaa.gov/xml/TWOAT.xml",
    "atlantic_basin_rss": "https://www.nhc.noaa.gov/index-at.xml",
}


def main() -> int:
    parser = robotparser.RobotFileParser()
    parser.set_url(ROBOTS)
    parser.read()
    allowed = {name: parser.can_fetch(USER_AGENT, url) for name, url in TARGETS.items()}
    result = {
        "project": "WORLD SIGNALS",
        "dataset": "NHC_ATLANTIC_SEASON_CF_ROBOTS_PROBE",
        "version": "0.1",
        "robots_url": ROBOTS,
        "user_agent": USER_AGENT,
        "target_path_access": allowed,
        "all_required_paths_allowed": all(allowed.values()),
        "policy": "FAIL_CLOSED_IF_ANY_REQUIRED_PATH_DISALLOWED",
        "opec_quarantine_respected": True,
        "source_body_retained": False,
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not result["all_required_paths_allowed"]:
        raise SystemExit("NHC crawler policy does not allow all bounded CF paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
