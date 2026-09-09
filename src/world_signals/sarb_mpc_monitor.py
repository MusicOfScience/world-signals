from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from zoneinfo import ZoneInfo

from .adapters.sarb_rss import SARBPublicationItem

SARB_TIMEZONE="Africa/Johannesburg"
SARB_SERIES_ID="WSER-REG-ZA-SARB"
CANONICAL_SOURCE_ID="WSSRC-REG-006"
MONITOR_SOURCE_ID="WSSRC-REG-013"


def _stable_hash(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":"))
    return sha256(raw.encode()).hexdigest()


def _scope(records: list[dict], config: dict) -> tuple[dict[str,dict],dict[tuple[int,int],dict]]:
    ids=list(config.get("canonical_occurrence_ids") or [])
    identities=config.get("statement_identity_by_occurrence_id")
    if len(ids)!=2 or len(set(ids))!=2 or not isinstance(identities,dict) or set(identities)!=set(ids):
        raise ValueError("SARB RSS requires exact two-occurrence identity map")
    by_id={r.get("occurrence_id"):r for r in records if r.get("occurrence_id") in set(ids)}
    if set(by_id)!=set(ids):
        raise ValueError("SARB RSS configured occurrence missing from Canonical")
    by_identity={}
    for oid in ids:
        ident=identities[oid]
        year=ident.get("year"); month=ident.get("month"); dt=ident.get("announcement_datetime")
        if not isinstance(year,int) or not isinstance(month,int) or not isinstance(dt,str):
            raise ValueError(f"SARB RSS invalid identity config for {oid}")
        if (year,month) in by_identity:
            raise ValueError("SARB RSS duplicate configured year/month identity")
        row=by_id[oid]
        checks={"series_id":SARB_SERIES_ID,"source_id":CANONICAL_SOURCE_ID,"region":"Africa","jurisdiction":"South Africa","source_timezone":SARB_TIMEZONE,"time_precision":"MINUTE","timing_type":"LOCAL_DATETIME","time_basis":"EXPLICIT_AUTHORITATIVE_SCHEDULE","start_local":dt,"publication_datetime":dt}
        for key,expected in checks.items():
            if row.get(key)!=expected:
                raise ValueError(f"SARB Canonical scope drift for {oid} {key}: {row.get(key)!r}")
        by_identity[(year,month)]=row
    gates=("schedule_authority","clock_authority","lifecycle_authority","certainty_authority","canonical_datetime_mutation_allowed","automatic_item_link_fetch_allowed","automatic_schedule_fetch_allowed","automatic_new_occurrence_creation_allowed","automatic_live_or_analysis_promotion_allowed","automatic_commit_allowed")
    if config.get("source_id")!=MONITOR_SOURCE_ID or any(config.get(k) is not False for k in gates):
        raise ValueError("SARB RSS authority/write gate drift")
    return by_id,by_identity


def _local_pubdate(item: SARBPublicationItem) -> tuple[str,str]:
    dt=datetime.fromisoformat(item.pub_date.replace("Z","+00:00")).astimezone(ZoneInfo(SARB_TIMEZONE))
    return dt.isoformat(),dt.date().isoformat()


def sarb_mpc_rss_review_candidates(records: list[dict], items: list[SARBPublicationItem], config: dict) -> tuple[list[dict],list[dict]]:
    by_id,by_identity=_scope(records,config)
    candidates=[]; observations=[]; matched=set()
    for item in items:
        if item.mpc_year is None:
            continue
        row=by_identity.get((item.mpc_year,item.mpc_month))
        if row is None:
            observations.append({"type":"SARB_MPC_STATEMENT_OUTSIDE_CONFIGURED_SCOPE","title":item.title,"link":item.link,"pubDate":item.pub_date,"event_state_inference":"NONE","automatic_commit_allowed":False})
            continue
        oid=row["occurrence_id"]
        if oid in matched:
            raise ValueError(f"multiple SARB RSS items mapped to {oid}")
        matched.add(oid)
        local_iso,local_date=_local_pubdate(item)
        expected_date=row["start_local"][:10]
        if row.get("lifecycle_status")=="COMPLETED":
            observations.append({"type":"SARB_COMPLETED_OCCURRENCE_STATEMENT_PRESENT_NO_LIFECYCLE_ACTION","occurrence_id":oid,"rss_pubdate":item.pub_date,"rss_pubdate_local":local_iso,"event_state_inference":"NONE","automatic_commit_allowed":False})
            continue
        mismatch=local_date!=expected_date
        evidence={"feed_title":item.title,"feed_link":item.link,"feed_category":item.category,"feed_guid":item.guid,"rss_pubdate":item.pub_date,"rss_pubdate_local":local_iso,"rss_publication_civil_date":local_date,"canonical_announcement_date":expected_date,"rss_pubdate_is_canonical_clock_authority":False,"canonical_source_id":CANONICAL_SOURCE_ID}
        digest=_stable_hash({"occurrence_id":oid,**evidence})
        candidates.append({"candidate_id":"WSRC-SARB-RSS-"+digest[:16],"candidate_type":"SARB_MPC_PUBLICATION_DATE_MISMATCH_REVIEW" if mismatch else "SARB_MPC_STATEMENT_PUBLICATION_EVIDENCE","source_id":MONITOR_SOURCE_ID,"occurrence_ids":[oid],"old_value":{"lifecycle_status":row.get("lifecycle_status"),"start_local":row.get("start_local"),"publication_datetime":row.get("publication_datetime"),"canonical_source_id":CANONICAL_SOURCE_ID},"new_value":evidence,"review_state":"PENDING_AUTHORITATIVE_SARB_MPC_PUBLICATION_REVIEW","candidate_origin":"LIVE_READ_ONLY_MONITOR","event_state_inference":"NONE","automatic_commit_allowed":False,"completion_requires_review":True,"canonical_datetime_mutation_allowed":False})
        observations.append({"type":"SARB_MPC_STATEMENT_MATCHED_REVIEW_REQUIRED","occurrence_id":oid,"publication_date_matches_canonical":not mismatch,"rss_pubdate_is_canonical_clock_authority":False,"event_state_inference":"NONE","automatic_commit_allowed":False})
    observations.append({"type":"SARB_RSS_ABSENCE_HAS_NO_SCHEDULE_LIFECYCLE_DELAY_CANCELLATION_OR_CERTAINTY_SEMANTICS","configured_occurrence_count":len(by_id),"matched_occurrence_count":len(matched),"event_state_inference":"NONE","automatic_commit_allowed":False})
    return candidates,observations
