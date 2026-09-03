from __future__ import annotations
from dataclasses import dataclass, asdict
from hashlib import sha256
import json

PROTECTED = ("occurrence_id", "series_id", "canonical_name", "category", "jurisdiction", "institution", "source_id")

@dataclass
class ReviewCandidate:
    candidate_id: str
    occurrence_id: str
    diff_type: str
    old_value: dict
    new_value: dict
    source_assertion: dict
    review_state: str = "PENDING_REVIEW"
    automatic_commit_allowed: bool = False

    def as_dict(self) -> dict:
        return asdict(self)

def protected_digest(record: dict) -> str:
    payload={k:record.get(k) for k in PROTECTED}
    return sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()

def compare_assertion(record: dict, assertion: dict) -> ReviewCandidate | None:
    """Compare an authoritative assertion to one occurrence. Never mutates the record."""
    fields=("start_local", "end_local", "certainty_status", "lifecycle_status")
    old={k:record.get(k) for k in fields}
    new={k:assertion.get(k, record.get(k)) for k in fields}
    changed={k for k in fields if old[k] != new[k]}
    if not changed:
        return None
    if changed <= {"lifecycle_status"}:
        dtype="LIFECYCLE_CHANGED"
    elif changed <= {"certainty_status"}:
        dtype="CERTAINTY_CHANGED"
    elif changed & {"start_local", "end_local"}:
        dtype="DATE_OR_TIME_CHANGED"
    else:
        dtype="MULTI_FIELD_CHANGED"
    raw=f"{record.get('occurrence_id')}|{dtype}|{json.dumps(new,sort_keys=True)}"
    return ReviewCandidate(
        candidate_id="WSRC-"+sha256(raw.encode()).hexdigest()[:16],
        occurrence_id=record["occurrence_id"],
        diff_type=dtype,
        old_value=old,
        new_value=new,
        source_assertion=assertion,
    )
