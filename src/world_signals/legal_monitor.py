from __future__ import annotations

from hashlib import sha256
import json


def _stable_hash(value: object) -> str:
    raw=json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False)
    return sha256(raw.encode("utf-8")).hexdigest()


def cbam_legal_milestone_review_candidate(
    rule: object,
    config: dict,
) -> tuple[dict | None, dict]:
    """Compare one parsed CBAM legal milestone with its reviewed baseline.

    The immutable legal text supplies semantic provenance. A semantic change is
    review evidence only: it never mutates the canonical occurrence directly.
    Current-law amendment/corrigendum/consolidation discovery is handled by the
    separate Cellar topology sentinel for the relevant act.
    """
    current=rule.as_dict() if hasattr(rule,"as_dict") else dict(rule)
    baseline=(config.get("baseline") or {}).get("rule") or {}
    baseline_hash=(config.get("baseline") or {}).get("rule_sha256") or baseline.get("rule_sha256")
    current_hash=current.get("rule_sha256") or _stable_hash(current)
    adapter_id=config.get("adapter_id") or "EU_CBAM_LEGAL_MILESTONE"

    if baseline_hash and current_hash == baseline_hash:
        return None,{
            "type":"CBAM_LEGAL_MILESTONE_NO_CHANGE",
            "adapter_id":adapter_id,
            "celex":current.get("celex"),
            "rule_id":current.get("rule_id"),
            "legal_locator":current.get("legal_locator"),
            "milestone_date":current.get("milestone_date"),
            "rule_sha256":current_hash,
        }

    payload={
        "celex":current.get("celex"),
        "rule_id":current.get("rule_id"),
        "legal_locator":current.get("legal_locator"),
        "milestone_date":current.get("milestone_date"),
        "rule_sha256":current_hash,
    }
    candidate_hash=_stable_hash({"adapter_id":adapter_id,"payload":payload})
    candidate={
        "candidate_id":"WSRC-EU-CBAM-"+candidate_hash[:16],
        "candidate_type":"LEGAL_MILESTONE_RULE_CHANGED",
        "adapter_id":adapter_id,
        "source_id":config.get("source_id"),
        "occurrence_ids":config.get("canonical_occurrence_ids") or [],
        "old_value":baseline,
        "new_value":payload,
        "review_state":"PENDING_CBAM_LEGAL_MILESTONE_REVIEW",
        "candidate_origin":"LIVE_READ_ONLY_MONITOR",
        "automatic_commit_allowed":False,
    }
    return candidate,{
        "type":"CBAM_LEGAL_MILESTONE_CHANGED",
        "adapter_id":adapter_id,
        "baseline_hash":baseline_hash,
        "current_hash":current_hash,
    }


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
            "adapter_id":config.get("adapter_id"),
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
    candidate_hash=_stable_hash({
        "adapter_id":config.get("adapter_id"),
        "payload":payload,
    })
    candidate={
        "candidate_id":"WSRC-EU-CELLAR-"+candidate_hash[:16],
        "candidate_type":"LEGAL_STATE_TOPOLOGY_CHANGED",
        "adapter_id":config.get("adapter_id"),
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
        "adapter_id":config.get("adapter_id"),
        "baseline_hash":baseline_hash,
        "current_hash":current_hash,
    }
