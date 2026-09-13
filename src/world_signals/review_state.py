from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable


OPAQUE_CANDIDATE_MARKERS=("LEGAL","TOPOLOGY","RULE","CLAUSE")


def _stable_json(value: Any) -> str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def _digest(value: Any) -> str:
    return sha256(_stable_json(value).encode("utf-8")).hexdigest()


def _candidate_type(candidate: dict) -> str:
    value=candidate.get("candidate_type") or candidate.get("diff_type")
    if not value:
        raise ValueError(f"candidate {candidate.get('candidate_id')} missing candidate type")
    return str(value)


def _occurrence_ids(candidate: dict) -> list[str]:
    values=candidate.get("occurrence_ids") or []
    if candidate.get("occurrence_id"):
        values=list(values)+[candidate["occurrence_id"]]
    out=sorted({str(value) for value in values if value})
    if not out:
        raise ValueError(f"candidate {candidate.get('candidate_id')} missing occurrence scope")
    return out


def _source_id(candidate: dict) -> str | None:
    if candidate.get("source_id"):
        return str(candidate["source_id"])
    assertion=candidate.get("source_assertion") or {}
    return str(assertion["source_id"]) if assertion.get("source_id") else None


def _is_opaque_candidate(candidate_type: str) -> bool:
    upper=candidate_type.upper()
    return any(marker in upper for marker in OPAQUE_CANDIDATE_MARKERS)


def _changed_fields(candidate: dict) -> tuple[list[str],dict[str,Any]]:
    old=candidate.get("old_value")
    new=candidate.get("new_value")
    if not isinstance(old,dict) or not isinstance(new,dict):
        raise ValueError(f"candidate {candidate.get('candidate_id')} lacks dictionary old/new values")
    fields=sorted(key for key in set(old)|set(new) if old.get(key)!=new.get(key))
    if not fields:
        raise ValueError(f"candidate {candidate.get('candidate_id')} proposes no material old/new difference")
    return fields,{key:new.get(key) for key in fields}


def proposition_identity(candidate: dict) -> dict:
    """Return a stable review proposition identity without exposing evidence payloads."""
    candidate_id=candidate.get("candidate_id")
    if not candidate_id:
        raise ValueError("candidate missing candidate_id")
    if candidate.get("automatic_commit_allowed") is not False:
        raise ValueError(f"candidate {candidate_id} does not explicitly prohibit automatic commit")

    candidate_type=_candidate_type(candidate)
    occurrence_ids=_occurrence_ids(candidate)

    if _is_opaque_candidate(candidate_type):
        proposed=candidate.get("new_value")
        if proposed is None:
            raise ValueError(f"opaque candidate {candidate_id} missing proposed rule state")
        identity_mode="OPAQUE_RULE_PROPOSITION"
        identity_payload={
            "identity_mode":identity_mode,
            "occurrence_ids":occurrence_ids,
            "candidate_type":candidate_type,
            "proposed_rule_state":proposed,
        }
        public_fields=["OPAQUE_RULE_STATE"]
        proposed_values=None
    else:
        fields,proposed_values=_changed_fields(candidate)
        identity_mode="CANONICAL_FIELD_PROPOSITION"
        identity_payload={
            "identity_mode":identity_mode,
            "occurrence_ids":occurrence_ids,
            "proposed_values":proposed_values,
        }
        public_fields=fields

    proposition_digest=_digest(identity_payload)
    return {
        "review_item_id":"WSRV-"+proposition_digest[:20],
        "identity_mode":identity_mode,
        "occurrence_ids":occurrence_ids,
        "candidate_type":candidate_type,
        "source_id":_source_id(candidate),
        "candidate_id":str(candidate_id),
        "proposed_change_fields":public_fields,
        "proposition_digest":proposition_digest,
        "_proposed_values":proposed_values,
    }


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid ISO timestamp: {value}") from exc
    if parsed.tzinfo is None:
        parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _canonical_alignment(item: dict,record_map: dict[str,dict]) -> str:
    if item["identity_mode"]!="CANONICAL_FIELD_PROPOSITION":
        return "NOT_EVALUABLE_OPAQUE_RULE"
    proposed=item.get("_proposed_values") or {}
    records=[record_map.get(occurrence_id) for occurrence_id in item["occurrence_ids"]]
    if any(record is None for record in records):
        return "OCCURRENCE_SCOPE_NOT_FOUND"
    aligned=all(all(record.get(field)==value for field,value in proposed.items()) for record in records if record)
    return "ALIGNED_WITH_CANONICAL" if aligned else "PROPOSAL_DIFFERS_FROM_CANONICAL"


def _decision_map(decisions: dict,allowed_states: set[str]) -> dict[str,list[dict]]:
    grouped: dict[str,list[dict]]={}
    for decision in decisions.get("decisions") or []:
        review_item_id=decision.get("review_item_id")
        state=decision.get("decision_state")
        decided_at=decision.get("decided_at")
        if not review_item_id or not state or not decided_at:
            raise ValueError("review decision requires review_item_id, decision_state and decided_at")
        if state not in allowed_states:
            raise ValueError(f"unsupported review decision state: {state}")
        _parse_time(decided_at)
        grouped.setdefault(str(review_item_id),[]).append(decision)
    for values in grouped.values():
        values.sort(key=lambda item:_parse_time(item["decided_at"]) or datetime.min.replace(tzinfo=timezone.utc))
    return grouped


def _ledger_links(change_ledger: dict) -> dict[str,list[dict]]:
    links: dict[str,list[dict]]={}
    for change in change_ledger.get("changes") or []:
        review_item_id=change.get("origin_review_item_id")
        if review_item_id:
            links.setdefault(str(review_item_id),[]).append(change)
    return links


def _operator_guidance(item: dict) -> tuple[str,str,str]:
    """Derive review routing metadata without granting action authority."""
    recurrence="REOBSERVED" if int(item.get("observation_count") or 0)>1 else "FIRST_OBSERVATION"
    state=item.get("state")
    if state=="CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION":
        return recurrence,"RECONCILIATION_REQUIRED","RECONCILE_CANONICAL_ALIGNMENT_AND_REVIEW_LEDGER"
    if state=="APPROVED_FOR_CANONICAL_COMMIT":
        return recurrence,"COMMIT_HANDOFF_REQUIRED","PREPARE_SEPARATELY_REVIEWED_CANONICAL_TRANSACTION"
    if item.get("reobserved_after_decision"):
        return recurrence,"REOBSERVED_AFTER_DECISION","REVIEW_PRIOR_DECISION_BEFORE_ANY_REOPEN"
    if state=="PENDING_REVIEW":
        attention="REPEATED_DECISION_REQUIRED" if recurrence=="REOBSERVED" else "DECISION_REQUIRED"
        return recurrence,attention,"VERIFY_AUTHORITATIVE_EVIDENCE_AND_RECORD_REVIEW_DECISION"
    return recurrence,"NO_ACTIVE_ACTION","PRESERVE_REVIEW_RECORD"


def reduce_review_state(
    runs: Iterable[dict],
    *,
    canonical_records: list[dict],
    decisions: dict,
    change_ledger: dict,
    contract: dict,
    generated_at: str | None=None,
) -> dict:
    """Reduce retained monitor candidate observations into stable review items.

    This is intentionally not a permanent queue. It is a deterministic view over
    retained run evidence plus explicitly reviewed manual decisions.
    """
    activation=(contract.get("activation") or {})
    activation_run=int(activation.get("activation_after_run_number") or 0)
    manual_states=set(contract.get("manual_decision_states") or [])
    decision_map=_decision_map(decisions,manual_states)
    ledger_links=_ledger_links(change_ledger)
    record_map={record.get("occurrence_id"):record for record in canonical_records if record.get("occurrence_id")}

    normalized_runs=[]
    for run in runs:
        run_number=int(run.get("run_number") or 0)
        if run_number<=activation_run:
            continue
        run_at=run.get("run_at")
        _parse_time(run_at)
        normalized_runs.append({
            "run_number":run_number,
            "run_id":str(run.get("run_id")) if run.get("run_id") is not None else None,
            "run_at":run_at,
            "candidates":list(run.get("candidates") or []),
        })
    normalized_runs.sort(key=lambda run:(run["run_number"],run.get("run_at") or ""))

    items: dict[str,dict]={}
    for run in normalized_runs:
        for candidate in run["candidates"]:
            identity=proposition_identity(candidate)
            review_item_id=identity["review_item_id"]
            item=items.get(review_item_id)
            if item is None:
                item={
                    "review_item_id":review_item_id,
                    "identity_mode":identity["identity_mode"],
                    "occurrence_ids":identity["occurrence_ids"],
                    "candidate_types":set(),
                    "source_ids":set(),
                    "candidate_ids":set(),
                    "first_observed_at":run["run_at"],
                    "last_observed_at":run["run_at"],
                    "observation_count":0,
                    "first_run_number":run["run_number"],
                    "last_run_number":run["run_number"],
                    "proposed_change_fields":identity["proposed_change_fields"],
                    "proposition_digest":identity["proposition_digest"],
                    "state":"PENDING_REVIEW",
                    "last_decision_state":None,
                    "decided_at":None,
                    "canonical_alignment_state":None,
                    "reobserved_after_decision":False,
                    "automatic_commit_allowed":False,
                    "_proposed_values":identity.get("_proposed_values"),
                }
                items[review_item_id]=item
            elif item["proposition_digest"]!=identity["proposition_digest"]:
                raise ValueError(f"review item digest collision for {review_item_id}")

            item["candidate_types"].add(identity["candidate_type"])
            if identity.get("source_id"):
                item["source_ids"].add(identity["source_id"])
            item["candidate_ids"].add(identity["candidate_id"])
            item["observation_count"]+=1
            if _parse_time(run["run_at"]) < _parse_time(item["first_observed_at"]):
                item["first_observed_at"]=run["run_at"]
                item["first_run_number"]=run["run_number"]
            if _parse_time(run["run_at"]) >= _parse_time(item["last_observed_at"]):
                item["last_observed_at"]=run["run_at"]
                item["last_run_number"]=run["run_number"]

    for review_item_id,item in items.items():
        decisions_for_item=decision_map.get(review_item_id) or []
        if decisions_for_item:
            latest=decisions_for_item[-1]
            state=latest["decision_state"]
            item["last_decision_state"]=state
            item["decided_at"]=latest["decided_at"]
            item["state"]="PENDING_REVIEW" if state=="REOPENED" else state
            item["reobserved_after_decision"]=(
                _parse_time(item["last_observed_at"]) > _parse_time(latest["decided_at"])
            )

        links=ledger_links.get(review_item_id) or []
        alignment=_canonical_alignment(item,record_map)
        if links:
            item["state"]="COMMITTED"
            item["canonical_alignment_state"]="COMMITTED_WITH_REVIEW_LEDGER_LINK"
        elif alignment=="ALIGNED_WITH_CANONICAL":
            item["state"]="CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION"
            item["canonical_alignment_state"]="ALIGNED_WITH_CANONICAL_NO_REVIEW_LEDGER_LINK"
        else:
            item["canonical_alignment_state"]=alignment

        recurrence,attention,next_action=_operator_guidance(item)
        item["recurrence_state"]=recurrence
        item["operator_attention_class"]=attention
        item["operator_next_action"]=next_action

        item["candidate_types"]=sorted(item["candidate_types"])
        item["source_ids"]=sorted(item["source_ids"])
        item["candidate_ids"]=sorted(item["candidate_ids"])
        item.pop("_proposed_values",None)

    public_fields=set(contract.get("public_item_fields") or [])
    public_items=[]
    for item in items.values():
        public={key:item.get(key) for key in contract.get("public_item_fields") or []}
        unexpected=set(public)-public_fields
        if unexpected:
            raise ValueError(f"unexpected public review fields: {sorted(unexpected)}")
        public_items.append(public)

    state_order={
        "CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION":0,
        "PENDING_REVIEW":1,
        "APPROVED_FOR_CANONICAL_COMMIT":2,
        "DEFERRED":3,
        "REJECTED":4,
        "SUPERSEDED":5,
        "COMMITTED":6,
    }
    public_items.sort(key=lambda item:(state_order.get(str(item.get("state")),99),item.get("first_observed_at") or "",item["review_item_id"]))

    generated_at=generated_at or datetime.now(timezone.utc).isoformat()
    states={}
    for item in public_items:
        states[item["state"]]=states.get(item["state"],0)+1

    return {
        "project":"WORLD SIGNALS",
        "dataset":"RETAINED_REVIEW_CANDIDATE_STATE",
        "version":contract.get("version"),
        "generated_at":generated_at,
        "scope":"RETAINED_ACTIONS_ARTEFACT_HORIZON_NOT_PERMANENT_QUEUE",
        "activation_after_run_number":activation_run,
        "retention_days":(contract.get("retention_limit") or {}).get("current_monitor_artefact_retention_days"),
        "run_count_considered":len(normalized_runs),
        "first_run_number":normalized_runs[0]["run_number"] if normalized_runs else None,
        "last_run_number":normalized_runs[-1]["run_number"] if normalized_runs else None,
        "item_count":len(public_items),
        "state_counts":dict(sorted(states.items())),
        "items":public_items,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    }
