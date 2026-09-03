from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Iterable

from .review_state import proposition_identity
from .runtime_projection import prohibited_field_hits


def _stable_json(value: Any) -> str:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)


def checkpoint_sha256(checkpoint: dict) -> str:
    return sha256(_stable_json(checkpoint).encode("utf-8")).hexdigest()


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    if parsed.tzinfo is None:
        parsed=parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


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


def _canonical_alignment(item: dict,record_map: dict[str,dict]) -> str:
    if item.get("identity_mode")!="CANONICAL_FIELD_PROPOSITION":
        return "NOT_EVALUABLE_OPAQUE_RULE"
    proposed=item.get("canonical_proposed_values")
    if not isinstance(proposed,dict) or not proposed:
        raise ValueError(f"canonical checkpoint item {item.get('review_item_id')} missing canonical_proposed_values")
    expected_fields=sorted(item.get("proposed_change_fields") or [])
    if sorted(proposed)!=expected_fields:
        raise ValueError(f"canonical proposed-value field mismatch for {item.get('review_item_id')}")
    records=[record_map.get(occurrence_id) for occurrence_id in item.get("occurrence_ids") or []]
    if not records or any(record is None for record in records):
        return "OCCURRENCE_SCOPE_NOT_FOUND"
    aligned=all(all(record.get(field)==value for field,value in proposed.items()) for record in records if record)
    return "ALIGNED_WITH_CANONICAL" if aligned else "PROPOSAL_DIFFERS_FROM_CANONICAL"


def _validate_item_shape(item: dict,contract: dict) -> None:
    allowed=set(contract.get("checkpoint_item_fields") or [])
    unexpected=set(item)-allowed
    if unexpected:
        raise ValueError(f"checkpoint item {item.get('review_item_id')} has unexpected fields: {sorted(unexpected)}")
    missing=allowed-set(item)
    if missing:
        raise ValueError(f"checkpoint item {item.get('review_item_id')} missing fields: {sorted(missing)}")
    review_item_id=item.get("review_item_id")
    if not str(review_item_id).startswith("WSRV-"):
        raise ValueError(f"invalid review_item_id in checkpoint: {review_item_id}")
    if item.get("automatic_commit_allowed") is not False:
        raise ValueError(f"checkpoint item {review_item_id} does not explicitly prohibit automatic commit")
    if item.get("identity_mode")=="CANONICAL_FIELD_PROPOSITION":
        if not isinstance(item.get("canonical_proposed_values"),dict) or not item["canonical_proposed_values"]:
            raise ValueError(f"canonical checkpoint item {review_item_id} requires canonical_proposed_values")
    elif item.get("canonical_proposed_values") is not None:
        raise ValueError(f"opaque checkpoint item {review_item_id} must not persist raw proposed rule state")


def validate_checkpoint(checkpoint: dict,contract: dict) -> None:
    required=set(contract.get("checkpoint_required_fields") or [])
    missing=required-set(checkpoint)
    if missing:
        raise ValueError(f"checkpoint missing required fields: {sorted(missing)}")
    if checkpoint.get("project")!="WORLD SIGNALS" or checkpoint.get("dataset")!="DURABLE_REVIEW_CHECKPOINT":
        raise ValueError("unexpected checkpoint project/dataset")
    if checkpoint.get("automatic_canonical_commit") is not False or checkpoint.get("google_calendar_write") is not False:
        raise ValueError("checkpoint safety boundary violated")
    items=checkpoint.get("items") or []
    ids=[]
    for item in items:
        _validate_item_shape(item,contract)
        ids.append(item["review_item_id"])
    if len(ids)!=len(set(ids)):
        raise ValueError("duplicate review_item_id in checkpoint")
    if checkpoint.get("item_count")!=len(items):
        raise ValueError("checkpoint item_count mismatch")
    counts={}
    for item in items:
        counts[item["state"]]=counts.get(item["state"],0)+1
    if dict(sorted(counts.items()))!=(checkpoint.get("state_counts") or {}):
        raise ValueError("checkpoint state_counts mismatch")
    prohibited=set(contract.get("prohibited_checkpoint_fields") or [])
    hits=prohibited_field_hits(checkpoint,prohibited)
    if hits:
        raise ValueError("checkpoint contains prohibited fields: "+", ".join(hits))


def _delta_items(runs: Iterable[dict],covered_through: int) -> tuple[dict[str,dict],list[dict]]:
    items: dict[str,dict]={}
    normalized=[]
    for run in runs:
        run_number=int(run.get("run_number") or 0)
        if run_number<=covered_through:
            raise ValueError(
                f"checkpoint delta run {run_number} is not strictly after covered-through run {covered_through}"
            )
        run_at=run.get("run_at")
        _parse_time(run_at)
        normalized.append({"run_number":run_number,"run_id":str(run.get("run_id")),"run_at":run_at,"candidates":list(run.get("candidates") or [])})
    normalized.sort(key=lambda run:(run["run_number"],run["run_at"] or ""))

    for run in normalized:
        for candidate in run["candidates"]:
            identity=proposition_identity(candidate)
            review_item_id=identity["review_item_id"]
            current=items.get(review_item_id)
            canonical_values=identity.get("_proposed_values") if identity["identity_mode"]=="CANONICAL_FIELD_PROPOSITION" else None
            if current is None:
                current={
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
                    "canonical_proposed_values":canonical_values,
                    "state":"PENDING_REVIEW",
                    "last_decision_state":None,
                    "decided_at":None,
                    "canonical_alignment_state":None,
                    "reobserved_after_decision":False,
                    "automatic_commit_allowed":False,
                }
                items[review_item_id]=current
            else:
                if current["proposition_digest"]!=identity["proposition_digest"]:
                    raise ValueError(f"review-item digest collision inside checkpoint delta: {review_item_id}")
                if current["canonical_proposed_values"]!=canonical_values:
                    raise ValueError(f"canonical proposed values drift inside checkpoint delta: {review_item_id}")
            current["candidate_types"].add(identity["candidate_type"])
            if identity.get("source_id"):
                current["source_ids"].add(identity["source_id"])
            current["candidate_ids"].add(identity["candidate_id"])
            current["observation_count"]+=1
            if _parse_time(run["run_at"]) < _parse_time(current["first_observed_at"]):
                current["first_observed_at"]=run["run_at"]
                current["first_run_number"]=run["run_number"]
            if _parse_time(run["run_at"]) >= _parse_time(current["last_observed_at"]):
                current["last_observed_at"]=run["run_at"]
                current["last_run_number"]=run["run_number"]

    for item in items.values():
        item["candidate_types"]=sorted(item["candidate_types"])
        item["source_ids"]=sorted(item["source_ids"])
        item["candidate_ids"]=sorted(item["candidate_ids"])
    return items,normalized


def _merge_observation(existing: dict,delta: dict) -> dict:
    invariant=("review_item_id","identity_mode","occurrence_ids","proposed_change_fields","proposition_digest","canonical_proposed_values")
    for key in invariant:
        if existing.get(key)!=delta.get(key):
            raise ValueError(f"checkpoint proposition invariant changed for {existing.get('review_item_id')}: {key}")
    merged=dict(existing)
    merged["candidate_types"]=sorted(set(existing.get("candidate_types") or [])|set(delta.get("candidate_types") or []))
    merged["source_ids"]=sorted(set(existing.get("source_ids") or [])|set(delta.get("source_ids") or []))
    merged["candidate_ids"]=sorted(set(existing.get("candidate_ids") or [])|set(delta.get("candidate_ids") or []))
    merged["observation_count"]=int(existing.get("observation_count") or 0)+int(delta.get("observation_count") or 0)
    if _parse_time(delta.get("first_observed_at")) < _parse_time(existing.get("first_observed_at")):
        merged["first_observed_at"]=delta["first_observed_at"]
        merged["first_run_number"]=delta["first_run_number"]
    if _parse_time(delta.get("last_observed_at")) >= _parse_time(existing.get("last_observed_at")):
        merged["last_observed_at"]=delta["last_observed_at"]
        merged["last_run_number"]=delta["last_run_number"]
    return merged


def _refresh_states(items: dict[str,dict],canonical_records: list[dict],decisions: dict,change_ledger: dict,review_contract: dict) -> None:
    decision_map=_decision_map(decisions,set(review_contract.get("manual_decision_states") or []))
    links=_ledger_links(change_ledger)
    record_map={record.get("occurrence_id"):record for record in canonical_records if record.get("occurrence_id")}

    for review_item_id,item in items.items():
        previous_decision=item.get("last_decision_state")
        decisions_for_item=decision_map.get(review_item_id) or []
        if previous_decision and not decisions_for_item:
            raise ValueError(f"checkpoint item {review_item_id} has decision state absent from review_decisions.json")
        item["state"]="PENDING_REVIEW"
        item["last_decision_state"]=None
        item["decided_at"]=None
        item["reobserved_after_decision"]=False
        if decisions_for_item:
            latest=decisions_for_item[-1]
            state=latest["decision_state"]
            item["last_decision_state"]=state
            item["decided_at"]=latest["decided_at"]
            item["state"]="PENDING_REVIEW" if state=="REOPENED" else state
            item["reobserved_after_decision"]=(
                _parse_time(item.get("last_observed_at")) > _parse_time(latest["decided_at"])
            )

        ledger_for_item=links.get(review_item_id) or []
        alignment=_canonical_alignment(item,record_map)
        if ledger_for_item:
            item["state"]="COMMITTED"
            item["canonical_alignment_state"]="COMMITTED_WITH_REVIEW_LEDGER_LINK"
        elif alignment=="ALIGNED_WITH_CANONICAL":
            item["state"]="CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION"
            item["canonical_alignment_state"]="ALIGNED_WITH_CANONICAL_NO_REVIEW_LEDGER_LINK"
        else:
            item["canonical_alignment_state"]=alignment


def propose_checkpoint(
    checkpoint: dict,
    runs: Iterable[dict],
    *,
    canonical_records: list[dict],
    decisions: dict,
    change_ledger: dict,
    review_contract: dict,
    checkpoint_contract: dict,
    generated_at: str,
) -> dict:
    validate_checkpoint(checkpoint,checkpoint_contract)
    covered=int(checkpoint.get("covered_through_monitor_run_number") or 0)
    delta,normalized_runs=_delta_items(runs,covered)
    items={item["review_item_id"]:dict(item) for item in checkpoint.get("items") or []}
    for review_item_id,new_item in delta.items():
        if review_item_id in items:
            items[review_item_id]=_merge_observation(items[review_item_id],new_item)
        else:
            items[review_item_id]=new_item

    _refresh_states(items,canonical_records,decisions,change_ledger,review_contract)

    state_order={
        "CANONICAL_ALIGNMENT_REQUIRES_RECONCILIATION":0,
        "PENDING_REVIEW":1,
        "APPROVED_FOR_CANONICAL_COMMIT":2,
        "DEFERRED":3,
        "REJECTED":4,
        "SUPERSEDED":5,
        "COMMITTED":6,
    }
    output_items=sorted(items.values(),key=lambda item:(state_order.get(item.get("state"),99),item.get("first_observed_at") or "",item["review_item_id"]))
    counts={}
    for item in output_items:
        counts[item["state"]]=counts.get(item["state"],0)+1

    latest=normalized_runs[-1] if normalized_runs else None
    proposal={
        "project":"WORLD SIGNALS",
        "dataset":"DURABLE_REVIEW_CHECKPOINT",
        "version":checkpoint_contract.get("version"),
        "checkpoint_sequence":int(checkpoint.get("checkpoint_sequence") or 0)+1,
        "generated_at":generated_at,
        "covered_through_monitor_run_number":latest["run_number"] if latest else checkpoint.get("covered_through_monitor_run_number"),
        "covered_through_monitor_run_id":latest["run_id"] if latest else checkpoint.get("covered_through_monitor_run_id"),
        "covered_through_monitor_run_at":latest["run_at"] if latest else checkpoint.get("covered_through_monitor_run_at"),
        "previous_checkpoint_sha256":checkpoint_sha256(checkpoint),
        "item_count":len(output_items),
        "state_counts":dict(sorted(counts.items())),
        "items":output_items,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    }
    validate_checkpoint(proposal,checkpoint_contract)
    return proposal


def checkpoint_public_projection(checkpoint: dict,review_contract: dict,checkpoint_contract: dict) -> dict:
    validate_checkpoint(checkpoint,checkpoint_contract)
    allowed=review_contract.get("public_item_fields") or []
    public_items=[{key:item.get(key) for key in allowed} for item in checkpoint.get("items") or []]
    payload={
        "project":"WORLD SIGNALS",
        "dataset":"DURABLE_REVIEW_CHECKPOINT_PUBLIC_PROJECTION",
        "version":checkpoint.get("version"),
        "checkpoint_sequence":checkpoint.get("checkpoint_sequence"),
        "generated_at":checkpoint.get("generated_at"),
        "covered_through_monitor_run_number":checkpoint.get("covered_through_monitor_run_number"),
        "covered_through_monitor_run_id":checkpoint.get("covered_through_monitor_run_id"),
        "covered_through_monitor_run_at":checkpoint.get("covered_through_monitor_run_at"),
        "item_count":len(public_items),
        "state_counts":checkpoint.get("state_counts") or {},
        "items":public_items,
        "automatic_canonical_commit":False,
        "google_calendar_write":False,
    }
    prohibited=set(checkpoint_contract.get("prohibited_checkpoint_fields") or [])|{"canonical_proposed_values"}
    hits=prohibited_field_hits(payload,prohibited)
    if hits:
        raise ValueError("public checkpoint projection contains private/prohibited fields: "+", ".join(hits))
    return payload
