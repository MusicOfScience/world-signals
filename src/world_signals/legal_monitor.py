from __future__ import annotations

from hashlib import sha256
import json


def _stable_hash(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def cellar_legal_topology_review_candidate(
    topology: object,
    config: dict,
) -> tuple[dict | None, dict]:
    """Compare normalized Cellar legal topology with a reviewed baseline.

    A changed relation set is evidence that the legal state deserves review,
    not proof that a tracked event date changed. No canonical mutation occurs.
    """
    current=topology.as_dict() if hasattr(topology,"as_dict") else dict(topology)
    baseline_block=(config.get("baseline") or {}).get("cellar_legal_topology") or {}
    baseline_hash=(config.get("baseline") or {}).get("cellar_legal_topology_sha256")
    baseline_hash=baseline_hash or baseline_block.get("topology_sha256")
    current_hash=current.get("topology_sha256") or _stable_hash(current)

    if baseline_hash and current_hash == baseline_hash:
        return None,{
            "type":"CELLAR_LEGAL_TOPOLOGY_NO_CHANGE",
            "base_celex":current.get("base_celex"),
            "topology_sha256":current_hash,
            "amendment_count":len(current.get("amendment_target_uris") or []),
            "correction_count":len(current.get("correction_target_uris") or []),
            "consolidation_count":len(current.get("consolidation_target_uris") or []),
            "repeal_count":len(current.get("repeal_target_uris") or []),
        }

    payload={
        "base_celex":current.get("base_celex"),
        "amendment_target_uris":current.get("amendment_target_uris") or [],
        "correction_target_uris":current.get("correction_target_uris") or [],
        "consolidation_target_uris":current.get("consolidation_target_uris") or [],
        "repeal_target_uris":current.get("repeal_target_uris") or [],
        "topology_sha256":current_hash,
    }
    candidate_hash=_stable_hash(payload)
    candidate={
        "candidate_id":"WSRC-EU-CELLAR-"+candidate_hash[:16],
        "candidate_type":"LEGAL_STATE_TOPOLOGY_CHANGED",
        "source_id":config.get("source_id"),
        "occurrence_ids":config.get("canonical_occurrence_ids") or [],
        "old_value":baseline_block,
        "new_value":payload,
        "review_state":"PENDING_CELLAR_AMENDMENT_CORRIGENDUM_CONSOLIDATION_REVIEW",
        "candidate_origin":"LIVE_READ_ONLY_MONITOR",
        "automatic_commit_allowed":False,
    }
    return candidate,{
        "type":"CELLAR_LEGAL_TOPOLOGY_CHANGED",
        "baseline_hash":baseline_hash,
        "current_hash":current_hash,
    }
