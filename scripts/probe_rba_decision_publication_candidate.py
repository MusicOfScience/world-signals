#!/usr/bin/env python3
"""One-shot read-only Step 15B RBA decision publication candidate probe."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.adapters.base import AdapterError
from world_signals.adapters.rba_mpb_decision_rss import (
    RBA_DECISION_SERIES,
    RBA_MPB_DECISION_RSS_URL,
    RBA_ROBOTS_URL,
    build_result_candidate,
    classify_decision_item,
    feed_path_allowed_by_robots,
    fetch_exact_url,
    match_canonical_occurrence,
    parse_decision_page,
    parse_decision_rss,
    validate_decision_page_url,
)


def probe(occurrence_id: str) -> dict:
    result = {
        "mode": "READ_ONLY_CANDIDATE_PROBE",
        "production_writes": False,
        "requests": [],
        "candidate": None,
    }
    robots, robots_meta = fetch_exact_url(RBA_ROBOTS_URL, accept="text/plain,*/*;q=0.1")
    result["requests"].append({"role": "ROBOTS_POLICY", **robots_meta.as_dict()})
    if not feed_path_allowed_by_robots(robots):
        result["classification"] = "ROBOTS_DISALLOWS_RSS"
        return result

    feed, feed_meta = fetch_exact_url(
        RBA_MPB_DECISION_RSS_URL,
        accept="application/rss+xml, application/xml, text/xml;q=0.9",
    )
    if "xml" not in feed_meta.content_type.lower():
        raise AdapterError(f"RBA feed content-type is not XML: {feed_meta.content_type!r}")
    result["requests"].append({"role": "MEDIA_RELEASE_RSS", **feed_meta.as_dict()})
    items = parse_decision_rss(feed)
    eligible = [item for item in items if classify_decision_item(item) == "EXACT_TITLE"]
    result["feed_items"] = [
        {"item": item.as_dict(), "classification": classify_decision_item(item)}
        for item in items
    ]
    if len(eligible) != 1:
        result["classification"] = "NO_UNIQUE_EXACT_DECISION_ITEM"
        return result
    item = eligible[0]
    canonical = json.loads((ROOT / "data/canonical/registry.json").read_text(encoding="utf-8"))
    records = canonical.get("records", canonical.get("occurrences", []))
    scoped = [row for row in records if row.get("series_id") == RBA_DECISION_SERIES]
    match_state, occurrence = match_canonical_occurrence(item, scoped)
    if match_state != "MATCHED" or occurrence is None:
        result["classification"] = "FAIL_TO_REVIEW_" + match_state
        result["canonical_match"] = None
        return result
    if occurrence.get("occurrence_id") != occurrence_id:
        result["classification"] = "FAIL_TO_REVIEW_UNEXPECTED_CANONICAL_MATCH"
        result["canonical_match"] = {"occurrence_id": occurrence.get("occurrence_id")}
        return result
    if occurrence.get("series_id") != RBA_DECISION_SERIES:
        raise AdapterError("requested Canonical occurrence is not the RBA decision series")

    page_url = validate_decision_page_url(item.link)
    page, page_meta = fetch_exact_url(page_url, accept="text/html,application/xhtml+xml")
    if "text/html" not in page_meta.content_type.lower():
        raise AdapterError(f"linked RBA page content-type is not HTML: {page_meta.content_type!r}")
    result["requests"].append({"role": "LINKED_DECISION_STATEMENT", **page_meta.as_dict()})
    outcome = parse_decision_page(page, item=item, resolved_url=page_meta.resolved_url)
    detected_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    result["candidate"] = build_result_candidate(
        item=item,
        outcome=outcome,
        occurrence=occurrence,
        feed_transport_sha256=feed_meta.body_sha256,
        page_transport_sha256=page_meta.body_sha256,
        detected_at_utc=detected_at,
    )
    result["classification"] = "REVIEW_PENDING_CANDIDATE_GENERATED"
    result["canonical_match"] = {
        "occurrence_id": occurrence["occurrence_id"],
        "series_id": occurrence["series_id"],
        "lifecycle_status_unchanged": occurrence.get("lifecycle_status"),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-only-probe", action="store_true", required=True,
                        help="explicitly confirm one read-only request sequence; no repository writes")
    parser.add_argument("--occurrence-id", required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(probe(args.occurrence_id), sort_keys=True, indent=2))
    except AdapterError as exc:
        print(json.dumps({
            "classification": "SOURCE_HEALTH_ONLY",
            "error": str(exc),
            "production_writes": False,
            "event_state_inference": False,
        }, sort_keys=True, indent=2))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
