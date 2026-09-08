from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import re

from .adapters.japan_mof_rss import JapanMOFRSSItem

CANONICAL_SOURCE_ID = "WSSRC-FIS-007"
MONITOR_SOURCE_ID = "WSSRC-FIS-029"
JGB_SERIES_ID = "WSER-FIS-JP-JGB"
JAPAN_MOF_TIMEZONE = "Asia/Tokyo"

_RESULT_RE = re.compile(
    r"^Auction Result of (?P<tenor>\d+)-Year JGBs on (?P<date>[A-Za-z]+ \d{1,2}, \d{4})(?P<special> \(For JGB Market Special Participants\))?$",
    re.I,
)
_ANNOUNCEMENT_RE = re.compile(
    r"^Announcement of (?P<tenor>\d+)-year JGBs to Be Issued in (?P<month>[A-Za-z]+) (?P<year>\d{4})$",
    re.I,
)
_CANONICAL_TENOR_RE = re.compile(r"^Japan (?P<tenor>\d+)-year JGB auction$", re.I)


def _stable_hash(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_title_date(value: str) -> str:
    try:
        return datetime.strptime(value, "%B %d, %Y").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"unrecognised Japan MOF RSS auction-result date: {value!r}") from exc


def _tenor(record: dict) -> int:
    match = _CANONICAL_TENOR_RE.fullmatch(str(record.get("canonical_name") or ""))
    if not match:
        raise ValueError(f"JGB Canonical name no longer exposes tenor identity: {record.get('occurrence_id')}")
    return int(match.group("tenor"))


def _configured_scope(records: list[dict], config: dict) -> dict[str, dict]:
    configured = list(config.get("canonical_occurrence_ids") or [])
    if len(configured) != 10 or len(configured) != len(set(configured)):
        raise ValueError("Japan MOF JGB RSS configured scope must contain exactly 10 unique occurrence IDs")
    configured_set = set(configured)
    by_id = {r.get("occurrence_id"): r for r in records if r.get("occurrence_id") in configured_set}
    if set(by_id) != configured_set:
        raise ValueError("Japan MOF JGB RSS configured occurrence missing from Canonical")
    for occurrence_id in configured:
        row = by_id[occurrence_id]
        if row.get("source_id") != CANONICAL_SOURCE_ID:
            raise ValueError(f"Japan JGB Canonical source-role drift for {occurrence_id}")
        if row.get("series_id") != JGB_SERIES_ID:
            raise ValueError(f"Japan JGB series drift for {occurrence_id}")
        if row.get("source_timezone") != JAPAN_MOF_TIMEZONE:
            raise ValueError(f"Japan JGB timezone drift for {occurrence_id}")
        if row.get("time_precision") != "DAY":
            raise ValueError(f"Japan JGB time precision drift for {occurrence_id}")
        _tenor(row)
    if config.get("source_id") != MONITOR_SOURCE_ID:
        raise ValueError("Japan MOF JGB RSS monitor source identity drifted")
    return by_id


def is_jgb_related(item: JapanMOFRSSItem) -> bool:
    text = (item.title + " " + item.link).casefold()
    return "/policy/jgbs/" in text or "jgb" in text or "auction" in text


def _result_identity(item: JapanMOFRSSItem) -> tuple[int, str, bool] | None:
    match = _RESULT_RE.fullmatch(item.title)
    if not match:
        return None
    return int(match.group("tenor")), _parse_title_date(match.group("date")), bool(match.group("special"))


def _announcement_identity(item: JapanMOFRSSItem) -> tuple[int, int, int] | None:
    match = _ANNOUNCEMENT_RE.fullmatch(item.title)
    if not match:
        return None
    month = datetime.strptime(match.group("month"), "%B").month
    return int(match.group("tenor")), int(match.group("year")), month


def _calendar_change_notice(item: JapanMOFRSSItem) -> bool:
    text = item.title.casefold()
    return "calendar" in text and ("alteration" in text or "change" in text or "revision" in text)


def _result_candidate(record: dict, item: JapanMOFRSSItem, *, auction_date: str, tenor: int) -> dict:
    evidence = {
        "official_rss_title": item.title,
        "official_rss_link": item.link,
        "official_rss_guid": item.guid,
        "rss_publication_time_utc": item.pub_date_utc,
        "rss_publication_time_original": item.pub_date_original,
        "auction_date_stated_in_title": auction_date,
        "tenor_years": tenor,
        "canonical_start_local": record.get("start_local"),
        "canonical_source_id": record.get("source_id"),
        "rss_publication_time_is_not_auction_time": True,
    }
    digest = _stable_hash({"occurrence_id": record["occurrence_id"], **evidence})
    return {
        "candidate_id": "WSRC-JGB-RSS-" + digest[:16],
        "candidate_type": "JAPAN_MOF_JGB_AUCTION_RESULT_PUBLICATION_EVIDENCE",
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": [record["occurrence_id"]],
        "old_value": {
            "lifecycle_status": record.get("lifecycle_status"),
            "certainty_status": record.get("certainty_status"),
            "start_local": record.get("start_local"),
            "time_precision": record.get("time_precision"),
            "canonical_source_id": record.get("source_id"),
        },
        "new_value": evidence,
        "review_state": "PENDING_AUTHORITATIVE_JGB_RESULT_REVIEW",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "completion_requires_review": True,
        "canonical_clock_mutation_allowed": False,
    }


def _calendar_notice_candidate(scoped: list[dict], item: JapanMOFRSSItem) -> dict:
    occurrence_ids = sorted(r["occurrence_id"] for r in scoped if r.get("lifecycle_status") != "COMPLETED")
    evidence = {
        "official_rss_title": item.title,
        "official_rss_link": item.link,
        "official_rss_guid": item.guid,
        "rss_publication_time_utc": item.pub_date_utc,
        "manual_calendar_source_id_required": CANONICAL_SOURCE_ID,
        "automatic_calendar_html_fetch_allowed": False,
    }
    digest = _stable_hash({"occurrence_ids": occurrence_ids, **evidence})
    return {
        "candidate_id": "WSRC-JGB-CAL-" + digest[:16],
        "candidate_type": "JAPAN_MOF_JGB_CALENDAR_CHANGE_NOTICE_REQUIRES_MANUAL_SCHEDULE_REVIEW",
        "source_id": MONITOR_SOURCE_ID,
        "occurrence_ids": occurrence_ids,
        "old_value": {"canonical_schedule_source_id": CANONICAL_SOURCE_ID},
        "new_value": evidence,
        "review_state": "PENDING_MANUAL_JGB_CALENDAR_RECHECK",
        "candidate_origin": "LIVE_READ_ONLY_MONITOR",
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
        "date_change_requires_manual_authoritative_calendar_review": True,
    }


def japan_mof_jgb_rss_review_candidates(
    records: list[dict],
    items: list[JapanMOFRSSItem],
    config: dict,
) -> tuple[list[dict], list[dict]]:
    by_id = _configured_scope(records, config)
    scoped = list(by_id.values())
    candidates: list[dict] = []
    observations: list[dict] = []
    matched_standard_results: set[str] = set()

    by_result_identity: dict[tuple[int, str], dict] = {
        (_tenor(row), str(row.get("start_local"))): row for row in scoped
    }

    for item in items:
        result = _result_identity(item)
        if result is not None:
            tenor, auction_date, special = result
            record = by_result_identity.get((tenor, auction_date))
            if special:
                observations.append({
                    "type": "JAPAN_MOF_JGB_SPECIAL_PARTICIPANT_RESULT_CORROBORATION_ONLY",
                    "occurrence_id": record.get("occurrence_id") if record else None,
                    "tenor_years": tenor,
                    "auction_date": auction_date,
                    "title": item.title,
                    "guid": item.guid,
                    "rss_publication_time_utc": item.pub_date_utc,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
                continue
            if record is None:
                observations.append({
                    "type": "JAPAN_MOF_JGB_STANDARD_RESULT_OUTSIDE_CONFIGURED_SCOPE",
                    "tenor_years": tenor,
                    "auction_date": auction_date,
                    "title": item.title,
                    "guid": item.guid,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                })
                continue
            occurrence_id = record["occurrence_id"]
            if occurrence_id in matched_standard_results:
                raise ValueError(f"multiple standard MOF RSS results mapped to one Canonical JGB occurrence: {occurrence_id}")
            matched_standard_results.add(occurrence_id)
            if record.get("lifecycle_status") == "COMPLETED":
                observations.append({
                    "type": "JAPAN_MOF_JGB_COMPLETED_OCCURRENCE_RESULT_PRESENT_NO_LIFECYCLE_ACTION",
                    "occurrence_id": occurrence_id,
                    "tenor_years": tenor,
                    "auction_date": auction_date,
                    "canonical_source_id": record.get("source_id"),
                    "monitor_source_id": MONITOR_SOURCE_ID,
                    "rss_publication_time_utc": item.pub_date_utc,
                    "event_state_inference": "NONE",
                    "automatic_commit_allowed": False,
                    "canonical_lifecycle_already_reviewed": True,
                })
                continue
            candidates.append(_result_candidate(record, item, auction_date=auction_date, tenor=tenor))
            observations.append({
                "type": "JAPAN_MOF_JGB_STANDARD_RESULT_MATCHED_REVIEW_REQUIRED",
                "occurrence_id": occurrence_id,
                "tenor_years": tenor,
                "auction_date": auction_date,
                "rss_publication_time_utc": item.pub_date_utc,
                "rss_publication_time_is_not_auction_time": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        announcement = _announcement_identity(item)
        if announcement is not None:
            tenor, year, month = announcement
            matches = [
                row for row in scoped
                if _tenor(row) == tenor
                and isinstance(row.get("start_local"), str)
                and row["start_local"].startswith(f"{year:04d}-{month:02d}-")
            ]
            observations.append({
                "type": "JAPAN_MOF_JGB_ISSUANCE_ANNOUNCEMENT_OBSERVED_NO_SCHEDULE_MUTATION",
                "occurrence_id": matches[0]["occurrence_id"] if len(matches) == 1 else None,
                "tenor_years": tenor,
                "reference_year": year,
                "reference_month": month,
                "identity_ambiguous": len(matches) != 1,
                "title": item.title,
                "guid": item.guid,
                "rss_publication_time_utc": item.pub_date_utc,
                "announcement_title_does_not_establish_auction_date": True,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        if _calendar_change_notice(item):
            candidates.append(_calendar_notice_candidate(scoped, item))
            observations.append({
                "type": "JAPAN_MOF_JGB_CALENDAR_CHANGE_NOTICE_REVIEW_REQUIRED",
                "title": item.title,
                "guid": item.guid,
                "rss_publication_time_utc": item.pub_date_utc,
                "manual_calendar_recheck_required": True,
                "automatic_calendar_html_fetch_allowed": False,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })
            continue

        if is_jgb_related(item):
            observations.append({
                "type": "JAPAN_MOF_JGB_RSS_ITEM_UNCLASSIFIED_NO_EVENT_INFERENCE",
                "title": item.title,
                "guid": item.guid,
                "rss_publication_time_utc": item.pub_date_utc,
                "event_state_inference": "NONE",
                "automatic_commit_allowed": False,
            })

    observations.append({
        "type": "JAPAN_MOF_JGB_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_OR_CERTAINTY_SEMANTICS",
        "configured_occurrence_count": len(scoped),
        "matched_standard_result_count": len(matched_standard_results),
        "rolling_feed": True,
        "canonical_schedule_source_id": CANONICAL_SOURCE_ID,
        "event_state_inference": "NONE",
        "automatic_commit_allowed": False,
    })
    return candidates, observations
