from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from typing import Iterable

from .monitor import compare_assertion


def stable_hash(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def _parse_local(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def rba_fsr_review_candidates(records: list[dict], items: Iterable[object], config: dict) -> tuple[list[dict], list[dict]]:
    """Match positive RBA publication evidence to canonical FSR occurrences.

    Absence from the feed never cancels or completes an event. Only a positive
    feed item can generate a review candidate, and this function never mutates
    canonical records.
    """
    allowed=set(config.get("canonical_occurrence_ids") or [])
    max_days=int((config.get("matching") or {}).get("nearest_planned_occurrence_max_days",75))
    candidates=[]
    observations=[]
    scoped=[r for r in records if r.get("occurrence_id") in allowed]

    for item in items:
        pub_iso=getattr(item,"pub_date_iso",None)
        title=getattr(item,"title",None)
        link=getattr(item,"link",None)
        pub=_parse_local(pub_iso)
        if pub is None:
            observations.append({"type":"RBA_ITEM_UNDATED","title":title,"link":link})
            continue
        pub_naive=pub.replace(tzinfo=None)
        matches=[]
        for record in scoped:
            start=_parse_local(record.get("start_local"))
            if start is None or start.year != pub_naive.year:
                continue
            delta=abs((start.date()-pub_naive.date()).days)
            if delta <= max_days:
                matches.append((delta,record))
        matches.sort(key=lambda x:x[0])
        if not matches:
            observations.append({
                "type":"RBA_PUBLICATION_UNMATCHED",
                "title":title,"link":link,"publication_datetime":pub_iso,
            })
            continue
        if len(matches)>1 and matches[0][0] == matches[1][0]:
            observations.append({
                "type":"RBA_MATCH_AMBIGUOUS",
                "title":title,"publication_datetime":pub_iso,
                "occurrence_ids":[m[1].get("occurrence_id") for m in matches],
            })
            continue
        record=matches[0][1]
        assertion={
            "source_id":config.get("source_id"),
            "start_local":pub_naive.isoformat(timespec="seconds"),
            "lifecycle_status":"COMPLETED",
            "publication_datetime":pub_iso,
            "source_url":link,
            "source_title":title,
            "evidence_class":"POSITIVE_OFFICIAL_RSS_PUBLICATION",
        }
        candidate=compare_assertion(record,assertion)
        if candidate:
            data=candidate.as_dict()
            data["candidate_origin"]="LIVE_READ_ONLY_MONITOR"
            data["automatic_commit_allowed"]=False
            candidates.append(data)
        else:
            observations.append({
                "type":"RBA_PUBLICATION_ALREADY_REFLECTED",
                "occurrence_id":record.get("occurrence_id"),
                "publication_datetime":pub_iso,
            })
    return candidates,observations


def colombia_legal_input_review_candidate(rows: list[dict], config: dict) -> tuple[dict | None, dict]:
    """Compare the typed SUIN inventory row with a frozen baseline.

    The inventory is a presence/version sentinel only. A change requires
    clause-level SUIN verification and never directly changes the canonical
    budget deadline.
    """
    baseline=(config.get("baseline") or {}).get("critical_fields") or {}
    keys=list(baseline.keys())
    if len(rows) != 1:
        current={"row_count":len(rows),"rows":rows}
        current_hash=stable_hash(current)
        candidate={
            "candidate_id":"WSRC-LEGAL-"+current_hash[:16],
            "candidate_type":"LEGAL_INSTRUMENT_IDENTITY_OR_PRESENCE_CHANGED",
            "source_id":config.get("source_id"),
            "occurrence_ids":config.get("canonical_occurrence_ids") or [],
            "old_value":baseline,
            "new_value":current,
            "review_state":"PENDING_CLAUSE_LEVEL_SUIN_VERIFICATION",
            "automatic_commit_allowed":False,
        }
        return candidate,{"type":"COLOMBIA_LEGAL_SENTINEL_CHANGED","current_hash":current_hash}

    row=rows[0]
    current={k:row.get(k) for k in keys}
    current_hash=stable_hash(current)
    baseline_hash=(config.get("baseline") or {}).get("critical_fields_sha256") or stable_hash(baseline)
    if current_hash == baseline_hash:
        return None,{
            "type":"COLOMBIA_LEGAL_SENTINEL_NO_CHANGE",
            "current_hash":current_hash,
            "vigencia":current.get("vigencia"),
        }
    candidate={
        "candidate_id":"WSRC-LEGAL-"+current_hash[:16],
        "candidate_type":"LEGAL_INPUT_CHANGED",
        "source_id":config.get("source_id"),
        "occurrence_ids":config.get("canonical_occurrence_ids") or [],
        "old_value":baseline,
        "new_value":current,
        "review_state":"PENDING_CLAUSE_LEVEL_SUIN_VERIFICATION",
        "automatic_commit_allowed":False,
    }
    return candidate,{
        "type":"COLOMBIA_LEGAL_SENTINEL_CHANGED",
        "baseline_hash":baseline_hash,
        "current_hash":current_hash,
    }
