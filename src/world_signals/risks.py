"""Closed, reviewed Risk / Regime-State history contract.

This module is deliberately separate from ``risk_projection``.  The existing
projection is a Canonical-derived presentation lens; this contract models
reviewed current/historical state over Signals and Relationships.  It does not
score risk, forecast outcomes, mutate upstream layers or populate production.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import json
import re
from typing import Any


@dataclass(frozen=True)
class RiskValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


PROHIBITED_KEYS = {
    "probability", "probability_percent", "forecast", "forecast_horizon",
    "scenario_probability", "prediction_interval", "expected_future_value",
    "predicted_value", "target_date", "risk_score", "severity_score",
    "composite_score", "likelihood", "scenario_id", "resolution_date",
}
UTC_Z = timezone.utc

RISK_ALLOWED_TRANSITIONS = {
    "BASELINE": {"BASELINE", "LATENT", "EMERGING", "UNCERTAIN"},
    "LATENT": {"LATENT", "EMERGING", "ELEVATED", "EASING", "RESOLVED", "UNCERTAIN"},
    "EMERGING": {"EMERGING", "ELEVATED", "INTENSIFYING", "EASING", "RESOLVED", "UNCERTAIN"},
    "ELEVATED": {"ELEVATED", "INTENSIFYING", "PERSISTENT", "EASING", "RESOLVED", "UNCERTAIN"},
    "INTENSIFYING": {"INTENSIFYING", "ELEVATED", "PERSISTENT", "EASING", "RESOLVED", "UNCERTAIN"},
    "PERSISTENT": {"PERSISTENT", "INTENSIFYING", "EASING", "RESOLVED", "UNCERTAIN"},
    "EASING": {"EASING", "BASELINE", "EMERGING", "ELEVATED", "RESOLVED", "UNCERTAIN"},
    "RESOLVED": {"RESOLVED", "BASELINE", "UNCERTAIN"},
    "UNCERTAIN": {"UNCERTAIN", "BASELINE", "LATENT", "EMERGING", "ELEVATED"},
}
REGIME_ALLOWED_TRANSITIONS = {
    "BASELINE": {"BASELINE", "TRANSITIONING", "ESTABLISHED", "UNCERTAIN"},
    "TRANSITIONING": {"TRANSITIONING", "ESTABLISHED", "EXITING", "BASELINE", "UNCERTAIN"},
    "ESTABLISHED": {"ESTABLISHED", "EXITING", "TRANSITIONING", "UNCERTAIN"},
    "EXITING": {"EXITING", "BASELINE", "TRANSITIONING", "UNCERTAIN"},
    "UNCERTAIN": {"UNCERTAIN", "BASELINE", "TRANSITIONING", "ESTABLISHED", "EXITING"},
}


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _strings(value: Any) -> bool:
    return isinstance(value, list) and all(_text(item) for item in value)


def _utc(value: Any) -> datetime | None:
    if not _text(value):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != UTC_Z.utcoffset(parsed):
        return None
    return parsed.astimezone(UTC_Z)


def _all_keys(value: Any, path: str = "$") -> list[str]:
    hits: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in PROHIBITED_KEYS:
                hits.append(f"{path}.{key}")
            hits.extend(_all_keys(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            hits.extend(_all_keys(child, f"{path}[{index}]"))
    return hits


def _preflight(schema: Any, dataset: Any, signals: Any, relationships: Any,
               observations: Any, evidence: Any, canonical: Any) -> list[str]:
    errors: list[str] = []
    values = (schema, dataset, signals, relationships, observations, evidence, canonical)
    if not all(isinstance(value, dict) for value in values):
        return ["Risk/Regime inputs must be objects"]
    try:
        json.dumps(values, allow_nan=False)
    except (TypeError, ValueError):
        return ["Risk/Regime inputs must contain finite JSON values"]
    if schema.get("version") != "0.1":
        errors.append("unsupported Risk/Regime schema version")
    if dataset.get("dataset") != schema.get("dataset"):
        errors.append("Risk/Regime dataset identifier must match schema")
    if not isinstance(dataset.get("states"), list):
        errors.append("states must be a list")
    for data, key, id_key in (
        (signals, "signals", "signal_id"),
        (relationships, "relationships", "relationship_id"),
        (observations, "observations", "observation_id"),
        (evidence, "evidence", "evidence_id"),
        (canonical, "records", "occurrence_id"),
    ):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
            continue
        for row in data[key]:
            if not isinstance(row, dict) or not _text(row.get(id_key)):
                errors.append(f"{id_key} must be non-empty text")
            if key in {"signals", "relationships"} and isinstance(row, dict):
                if not _text(row.get("revision_id")):
                    errors.append(f"{id_key} revision_id must be non-empty text")
                if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
                    errors.append(f"{id_key} revision_number must be positive integer")
                if not _text(row.get("review_state")) or not _text(row.get("lifecycle_state")):
                    errors.append(f"{id_key} review/lifecycle state must be non-empty text")
    vocab = schema.get("controlled_vocabularies")
    if not isinstance(vocab, dict):
        errors.append("controlled_vocabularies must be an object")
        return errors
    required_vocab = (
        "state_class", "risk_state", "regime_state", "transition_type",
        "transition_direction", "convergence_state", "persistence", "trend_state",
        "materiality", "confidence", "review_state", "lifecycle_state",
        "expiry_mode", "threshold_type",
    )
    for key in required_vocab:
        if not _strings(vocab.get(key)) or not vocab[key]:
            errors.append(f"invalid Risk/Regime vocabulary {key}")

    required = set(schema.get("required_state_fields") or [])
    for row in dataset.get("states") if isinstance(dataset.get("states"), list) else []:
        if not isinstance(row, dict):
            errors.append("Risk/Regime state rows must be objects")
            continue
        if set(row) != required:
            errors.append("missing/unknown Risk/Regime fields; forecast/scenario fields are prohibited")
            continue
        for key in (
            "state_id", "revision_id", "title", "state_class", "system_domain",
            "current_state", "transition_type", "transition_direction", "persistence",
            "trend_state", "materiality", "confidence", "first_detected_at_utc",
            "state_effective_at_utc", "review_state", "lifecycle_state", "rationale",
            "alternative_interpretation", "revision_reason",
        ):
            if not _text(row.get(key)):
                errors.append(f"{key} must be non-empty text")
        if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
            errors.append("revision_number must be a positive integer")
        if row.get("previous_revision_id") is not None and not _text(row["previous_revision_id"]):
            errors.append("previous_revision_id must be null or non-empty text")
        if row.get("previous_state") is not None and not _text(row["previous_state"]):
            errors.append("previous_state must be null or non-empty text")
        for key in ("jurisdictions", "contributing_domains", "falsification_conditions", "supporting_observation_ids"):
            if not _strings(row.get(key)):
                errors.append(f"{key} must be a list of strings")
        for key in (
            "supporting_signal_revisions", "supporting_relationship_revisions",
            "contradictory_signal_revisions", "contradictory_relationship_revisions",
        ):
            pins = row.get(key)
            if not isinstance(pins, list):
                errors.append(f"{key} must be a list")
            else:
                for pin in pins:
                    expected_keys = (
                        {"signal_id", "revision_id"}
                        if key.endswith("signal_revisions")
                        else {"relationship_id", "revision_id"}
                    )
                    object_key = "signal_id" if key.endswith("signal_revisions") else "relationship_id"
                    if not isinstance(pin, dict) or set(pin) != expected_keys:
                        errors.append(f"{key} contains an invalid revision pin")
                    elif not _text(pin.get("revision_id")) or not _text(pin.get(object_key)):
                        errors.append(f"{key} IDs must be non-empty text")
        for key in ("state_class", "transition_type", "transition_direction", "persistence", "trend_state", "materiality", "confidence", "review_state", "lifecycle_state"):
            if row.get(key) not in vocab[key]:
                errors.append(f"invalid {key}")
        states = vocab["risk_state"] if row.get("state_class") == "RISK_STATE" else vocab["regime_state"]
        if row.get("current_state") not in states:
            errors.append("current_state is not valid for state_class")
        if row.get("previous_state") is not None and row.get("previous_state") not in states:
            errors.append("previous_state is not valid for state_class")
        if _utc(row.get("first_detected_at_utc")) is None or _utc(row.get("state_effective_at_utc")) is None:
            errors.append("first_detected_at_utc and state_effective_at_utc must be exact UTC")
        convergence = row.get("convergence")
        if not isinstance(convergence, dict) or set(convergence) != {
            "state", "distinct_signal_count", "distinct_relationship_count",
            "distinct_observation_count", "distinct_provider_count", "distinct_domain_count",
            "distinct_mechanism_count", "rationale",
        }:
            errors.append("convergence has an invalid field set")
        elif convergence.get("state") not in vocab["convergence_state"] or not _text(convergence.get("rationale")):
            errors.append("convergence requires a controlled state and rationale")
        else:
            for key in (
                "distinct_signal_count", "distinct_relationship_count", "distinct_observation_count",
                "distinct_provider_count", "distinct_domain_count", "distinct_mechanism_count",
            ):
                if type(convergence.get(key)) is not int or convergence[key] < 0:
                    errors.append(f"convergence.{key} must be a non-negative integer")
        expiry = row.get("expiry")
        if not isinstance(expiry, dict) or set(expiry) != {"mode", "stale_after_days", "expires_at_utc", "review_due_at_utc", "condition"}:
            errors.append("expiry has an invalid field set")
        else:
            if expiry.get("mode") not in vocab["expiry_mode"] or not _text(expiry.get("condition")):
                errors.append("expiry requires a controlled mode and condition")
            if expiry.get("mode") == "STALE_AFTER" and (type(expiry.get("stale_after_days")) is not int or expiry["stale_after_days"] <= 0 or expiry.get("expires_at_utc") is not None or expiry.get("review_due_at_utc") is not None):
                errors.append("STALE_AFTER requires positive days and no fixed deadline")
            if expiry.get("mode") == "STALE_AFTER" and not row.get("supporting_observation_ids"):
                errors.append("STALE_AFTER requires explicit supporting observations for deterministic staleness")
            if expiry.get("mode") == "EXPLICIT_DATE" and (_utc(expiry.get("expires_at_utc")) is None or expiry.get("stale_after_days") is not None or expiry.get("review_due_at_utc") is not None):
                errors.append("EXPLICIT_DATE requires an exact expiry and no other deadline")
            if expiry.get("mode") == "REVIEW_REQUIRED" and (_utc(expiry.get("review_due_at_utc")) is None or expiry.get("stale_after_days") is not None or expiry.get("expires_at_utc") is not None):
                errors.append("REVIEW_REQUIRED requires an exact review deadline and no other deadline")
        threshold = row.get("threshold_basis")
        if not isinstance(threshold, dict) or set(threshold) != {"threshold_type", "description", "provenance"}:
            errors.append("threshold_basis has an invalid field set")
        elif threshold.get("threshold_type") not in vocab["threshold_type"] or not _text(threshold.get("description")) or not _text(threshold.get("provenance")):
            errors.append("threshold_basis requires type, description and provenance")
        provenance = row.get("review_provenance")
        if not isinstance(provenance, dict) or set(provenance) != {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}:
            errors.append("review_provenance has an invalid field set")
        elif not _text(provenance.get("created_by")) or _utc(provenance.get("created_at_utc")) is None:
            errors.append("review_provenance requires creator and exact UTC creation time")
        elif provenance.get("reviewed_at_utc") is not None and _utc(provenance.get("reviewed_at_utc")) is None:
            errors.append("reviewed_at_utc must be exact UTC or null")
        errors.extend(f"prohibited field: {path}" for path in _all_keys(row))
    return errors


def _indexes(signals: dict, relationships: dict, observations: dict, evidence: dict):
    signal_revisions = {row["revision_id"]: row for row in signals["signals"]}
    relationship_revisions = {row["revision_id"]: row for row in relationships["relationships"]}
    observation_by_id = {row["observation_id"]: row for row in observations["observations"]}
    evidence_by_id = {row["evidence_id"]: row for row in evidence["evidence"]}
    return signal_revisions, relationship_revisions, observation_by_id, evidence_by_id


def _revision_time(row: dict) -> datetime:
    provenance = row["review_provenance"]
    return _utc(provenance.get("reviewed_at_utc") or provenance["created_at_utc"])


def _pin_ids(pins: list[dict], id_key: str) -> set[str]:
    return {pin[id_key] for pin in pins}


def _lineage(row: dict, signal_revisions: dict, relationship_revisions: dict,
             observations: dict, evidence: dict):
    observation_ids = set(row["supporting_observation_ids"])
    evidence_ids: set[str] = set()
    domains: set[str] = set()
    mechanism_keys: set[str] = set()
    provider_keys: set[str] = set()
    for pin in row["supporting_signal_revisions"]:
        signal = signal_revisions.get(pin["revision_id"])
        if not signal:
            continue
        observation_ids.update(signal.get("observation_ids") or [])
        evidence_ids.update(signal.get("evidence_refs") or [])
        domains.update(signal.get("domains") or [])
    for pin in row["supporting_relationship_revisions"]:
        relationship = relationship_revisions.get(pin["revision_id"])
        if not relationship:
            continue
        observation_ids.update(relationship.get("supporting_observation_ids") or [])
        evidence_ids.update(relationship.get("supporting_evidence_refs") or [])
        domains.update(relationship.get("domains") or [])
        if _text(relationship.get("mechanism")):
            mechanism_keys.add(re.sub(r"\s+", " ", relationship["mechanism"].strip().lower()))
    for observation_id in list(observation_ids):
        observation = observations.get(observation_id)
        if observation:
            evidence_ids.update(observation.get("evidence_refs") or [])
    for evidence_id in evidence_ids:
        item = evidence.get(evidence_id)
        if not item:
            continue
        origins = item.get("origin_ids")
        if isinstance(origins, list) and origins:
            provider_keys.update(origin for origin in origins if _text(origin))
        elif _text(item.get("provider")):
            provider_keys.add(item["provider"].strip().lower())
    return observation_ids, evidence_ids, provider_keys, domains, mechanism_keys


def _validate_pins(row: dict, signal_revisions: dict, relationship_revisions: dict, errors: list[str]) -> None:
    for key, id_key, revision_map, label in (
        ("supporting_signal_revisions", "signal_id", signal_revisions, "Signal"),
        ("contradictory_signal_revisions", "signal_id", signal_revisions, "Signal"),
        ("supporting_relationship_revisions", "relationship_id", relationship_revisions, "Relationship"),
        ("contradictory_relationship_revisions", "relationship_id", relationship_revisions, "Relationship"),
    ):
        pins = row[key]
        pairs = [(pin[id_key], pin["revision_id"]) for pin in pins]
        if len(pairs) != len(set(pairs)):
            errors.append(f"{row['state_id']}: duplicate {label} revision pins cannot increase convergence")
        ids = [pair[0] for pair in pairs]
        if len(ids) != len(set(ids)):
            errors.append(f"{row['state_id']}: one {label} may not be represented by multiple revisions in one evidence set")
        for object_id, revision_id in pairs:
            item = revision_map.get(revision_id)
            if item is None or item.get(id_key) != object_id:
                errors.append(f"{row['state_id']}: unknown or mismatched {label} revision {object_id}/{revision_id}")


def _valid_transition(row: dict, errors: list[str]) -> None:
    state_class = row["state_class"]
    previous = row["previous_state"]
    current = row["current_state"]
    transition = row["transition_type"]
    direction = row["transition_direction"]
    if previous is None and transition != "INITIAL_ASSERTION":
        errors.append(f"{row['state_id']}: first revision requires INITIAL_ASSERTION")
    if previous is not None and transition == "INITIAL_ASSERTION":
        errors.append(f"{row['state_id']}: INITIAL_ASSERTION cannot follow a prior state")
    if previous is not None:
        allowed = (RISK_ALLOWED_TRANSITIONS if state_class == "RISK_STATE" else REGIME_ALLOWED_TRANSITIONS).get(previous, set())
        if current not in allowed:
            errors.append(f"{row['state_id']}: invalid {state_class} transition {previous} -> {current}")
    if previous == current and transition not in {"PERSISTENCE", "REASSESSMENT", "CONFLICT"}:
        errors.append(f"{row['state_id']}: unchanged state requires persistence/reassessment/conflict")
    if previous != current and transition in {"PERSISTENCE", "REASSESSMENT"}:
        errors.append(f"{row['state_id']}: changed state cannot use {transition}")
    if current == "BASELINE" and previous not in {None, "BASELINE"} and transition not in {"RETURN_TO_BASELINE", "REGIME_EXIT", "EASING"}:
        errors.append(f"{row['state_id']}: return to BASELINE requires an explicit return/exit transition")
    if state_class == "RISK_STATE" and previous == "RESOLVED" and current not in {"BASELINE", "UNCERTAIN"}:
        errors.append(f"{row['state_id']}: RESOLVED risk requires a new reviewed transition through baseline or uncertainty")
    if state_class == "REGIME_STATE" and previous == "ESTABLISHED" and current == "BASELINE" and transition != "REGIME_EXIT":
        errors.append(f"{row['state_id']}: established regime exit must be explicit")
    if direction == "UPWARD" and previous == current:
        errors.append(f"{row['state_id']}: upward transition requires a changed state")
    if direction == "DOWNWARD" and previous == current:
        errors.append(f"{row['state_id']}: downward transition requires a changed state")


def _validate_row(row: dict, schema: dict, indexes, errors: list[str]) -> None:
    signal_revisions, relationship_revisions, observation_by_id, evidence_by_id = indexes
    state_id = row["state_id"]
    _validate_pins(row, signal_revisions, relationship_revisions, errors)
    _valid_transition(row, errors)
    support_signal_ids = _pin_ids(row["supporting_signal_revisions"], "signal_id")
    contradiction_signal_ids = _pin_ids(row["contradictory_signal_revisions"], "signal_id")
    support_relationship_ids = _pin_ids(row["supporting_relationship_revisions"], "relationship_id")
    contradiction_relationship_ids = _pin_ids(row["contradictory_relationship_revisions"], "relationship_id")
    if support_signal_ids & contradiction_signal_ids:
        errors.append(f"{state_id}: Signal cannot be both supporting and contradictory")
    if support_relationship_ids & contradiction_relationship_ids:
        errors.append(f"{state_id}: Relationship cannot be both supporting and contradictory")
    for observation_id in row["supporting_observation_ids"]:
        if observation_id not in observation_by_id:
            errors.append(f"{state_id}: unknown supporting observation {observation_id}")
    observation_ids, evidence_ids, providers, domains, mechanisms = _lineage(
        row, signal_revisions, relationship_revisions, observation_by_id, evidence_by_id,
    )
    convergence = row["convergence"]
    expected_counts = {
        "distinct_signal_count": len(support_signal_ids),
        "distinct_relationship_count": len(support_relationship_ids),
        "distinct_observation_count": len(observation_ids),
        "distinct_provider_count": len(providers),
        "distinct_domain_count": len(domains),
        "distinct_mechanism_count": len(mechanisms),
    }
    if set(row["contributing_domains"]) != domains:
        errors.append(f"{state_id}: contributing_domains must equal derived upstream domains")
    for key, expected in expected_counts.items():
        if convergence[key] != expected:
            errors.append(f"{state_id}: {key} must equal derived lineage count {expected}")
    if convergence["state"] == "NONE" and any(expected_counts.values()):
        errors.append(f"{state_id}: non-empty evidence cannot have NONE convergence")
    if convergence["state"] == "BROAD_CONVERGENCE" and (len(domains) < 2 or len(providers) < 2):
        errors.append(f"{state_id}: BROAD_CONVERGENCE requires multiple domains and providers")
    if row["current_state"] in {"ELEVATED", "INTENSIFYING", "PERSISTENT", "TRANSITIONING", "ESTABLISHED", "EXITING"} and not (support_signal_ids or support_relationship_ids):
        errors.append(f"{state_id}: substantive current state requires reviewed Signal or Relationship support")
    created = _utc(row["review_provenance"]["created_at_utc"])
    reviewed = _utc(row["review_provenance"].get("reviewed_at_utc"))
    first_detected = _utc(row["first_detected_at_utc"])
    effective = _utc(row["state_effective_at_utc"])
    if created and first_detected and first_detected > created:
        errors.append(f"{state_id}: first_detected_at_utc cannot be after assessment creation")
    if created and effective and effective > created:
        errors.append(f"{state_id}: state_effective_at_utc cannot use future knowledge")
    if reviewed and created and reviewed < created:
        errors.append(f"{state_id}: review decision cannot predate creation")
    if row["review_state"] in {"ACCEPTED", "REJECTED"}:
        if not _text(row["review_provenance"].get("reviewed_by")) or reviewed is None or not _text(row["review_provenance"].get("decision_basis")):
            errors.append(f"{state_id}: accepted/rejected decision requires reviewer, timestamp and reason")
    elif any(row["review_provenance"].get(key) is not None for key in ("reviewed_by", "reviewed_at_utc", "decision_basis")):
        errors.append(f"{state_id}: unresolved review must not claim a completed decision")
    if row["review_state"] in {"CANDIDATE", "UNDER_REVIEW"} and row["lifecycle_state"] != "UNRESOLVED":
        errors.append(f"{state_id}: unaccepted state must be UNRESOLVED")
    if row["review_state"] == "REJECTED" and row["lifecycle_state"] != "WITHDRAWN":
        errors.append(f"{state_id}: rejected state must be WITHDRAWN")
    if row["review_state"] == "ACCEPTED" and row["lifecycle_state"] == "UNRESOLVED":
        errors.append(f"{state_id}: accepted state requires a resolved lifecycle")
    if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"} and row["review_state"] != "ACCEPTED":
        errors.append(f"{state_id}: active/weakening state requires accepted review")
    for key, revision_map, id_key in (
        ("supporting_signal_revisions", signal_revisions, "signal_id"),
        ("contradictory_signal_revisions", signal_revisions, "signal_id"),
        ("supporting_relationship_revisions", relationship_revisions, "relationship_id"),
        ("contradictory_relationship_revisions", relationship_revisions, "relationship_id"),
    ):
        for pin in row[key]:
            upstream = revision_map.get(pin["revision_id"])
            if not upstream:
                continue
            upstream_created = _utc(upstream.get("review_provenance", {}).get("created_at_utc"))
            if created and upstream_created and upstream_created > created:
                errors.append(f"{state_id}: later {id_key} revision cannot support an earlier assessment")
            if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"}:
                if upstream.get("review_state") != "ACCEPTED" or upstream.get("lifecycle_state") not in {"ACTIVE", "WEAKENING"}:
                    errors.append(f"{state_id}: rejected/withdrawn {id_key} cannot support an active state")
    for observation_id in observation_ids:
        observation = observation_by_id.get(observation_id)
        observed = _utc(observation.get("observed_at_utc")) if observation else None
        if created and observed and observed > created:
            errors.append(f"{state_id}: later observation cannot support an earlier assessment")
    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id)
        publication = item.get("publication_time", {}) if item else {}
        published = _utc(publication.get("published_at_utc")) if publication.get("published_at_utc") else None
        if published is None and _text(publication.get("published_date")):
            try:
                published = datetime.fromisoformat(publication["published_date"]).replace(tzinfo=UTC_Z)
            except ValueError:
                pass
        if created and published and published > created:
            errors.append(f"{state_id}: later evidence cannot support an earlier assessment")


def _validate_history(schema: dict, rows: list[dict], signals: dict, relationships: dict,
                      observations: dict, evidence: dict, canonical: dict,
                      *, previous_revisions: list[dict] | None = None) -> RiskValidationReport:
    errors: list[str] = []
    indexes = _indexes(signals, relationships, observations, evidence)
    by_state: dict[str, list[dict]] = {}
    revision_ids: set[str] = set()
    for row in rows:
        if row["revision_id"] in revision_ids:
            errors.append(f"duplicate Risk/Regime revision_id {row['revision_id']}")
        revision_ids.add(row["revision_id"])
        by_state.setdefault(row["state_id"], []).append(row)
        _validate_row(row, schema, indexes, errors)
    current = {row["revision_id"]: row for row in rows}
    if previous_revisions is not None:
        if not isinstance(previous_revisions, list):
            errors.append("previous_revisions must be a retained snapshot list")
        else:
            for old in previous_revisions:
                if not isinstance(old, dict) or not _text(old.get("revision_id")) or current.get(old["revision_id"]) != old:
                    errors.append("retained Risk/Regime revision was removed or rewritten")
    transitions = {
        "CANDIDATE": {"CANDIDATE", "UNDER_REVIEW"},
        "UNDER_REVIEW": {"UNDER_REVIEW", "ACCEPTED", "REJECTED"},
        "ACCEPTED": {"ACCEPTED", "UNDER_REVIEW"},
        "REJECTED": {"UNDER_REVIEW"},
    }
    for state_id, revisions in by_state.items():
        ordered = sorted(revisions, key=lambda row: row["revision_number"])
        if [row["revision_number"] for row in ordered] != list(range(1, len(ordered) + 1)):
            errors.append(f"{state_id}: revision numbers must be contiguous from 1")
        for index, row in enumerate(ordered):
            previous = ordered[index - 1] if index else None
            if previous is None:
                if row["previous_revision_id"] is not None or row["previous_state"] is not None:
                    errors.append(f"{state_id}: first revision cannot have predecessor metadata")
            else:
                if row["previous_revision_id"] != previous["revision_id"]:
                    errors.append(f"{state_id}: predecessor link is not preserved")
                if _revision_time(row) <= _revision_time(previous):
                    errors.append(f"{state_id}: revision time must strictly advance")
                if row["first_detected_at_utc"] != previous["first_detected_at_utc"]:
                    errors.append(f"{state_id}: first detection time must remain stable")
                if row["previous_state"] != previous["current_state"]:
                    errors.append(f"{state_id}: previous_state must preserve the prior assessment")
                if row["review_state"] not in transitions[previous["review_state"]]:
                    errors.append(f"{state_id}: invalid review transition")
                if previous["lifecycle_state"] in {"EXPIRED", "WITHDRAWN", "SUPERSEDED"} and row["lifecycle_state"] == "ACTIVE":
                    errors.append(f"{state_id}: terminal state requires reopening review before reactivation")
                if _utc(row["state_effective_at_utc"]) < _utc(previous["state_effective_at_utc"]):
                    errors.append(f"{state_id}: state effective time cannot move backwards")
    return RiskValidationReport(tuple(errors))


def validate_risk_state_history(
    schema: dict[str, Any], revisions: list[dict[str, Any]], signals: dict[str, Any],
    relationships: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any],
    canonical: dict[str, Any], *, previous_revisions: list[dict[str, Any]] | None = None,
) -> RiskValidationReport:
    """Validate synthetic/proposed history without production storage authority."""
    dataset = {
        "dataset": schema.get("dataset"),
        "version": schema.get("version"),
        "population_state": "CLOSED_NO_PRODUCTION_RISK_REGIME_STATES",
        "states": revisions,
    }
    errors = _preflight(schema, dataset, signals, relationships, observations, evidence, canonical)
    if errors:
        return RiskValidationReport(tuple(errors))
    return _validate_history(schema, revisions, signals, relationships, observations, evidence, canonical, previous_revisions=previous_revisions)


def validate_risk_states(schema: dict[str, Any], dataset: dict[str, Any], signals: dict[str, Any],
                         relationships: dict[str, Any], observations: dict[str, Any],
                         evidence: dict[str, Any], canonical: dict[str, Any]) -> RiskValidationReport:
    """Production gate: Risk/Regime population is intentionally closed."""
    errors = _preflight(schema, dataset, signals, relationships, observations, evidence, canonical)
    if errors:
        return RiskValidationReport(tuple(errors))
    if dataset.get("version") != schema.get("version"):
        errors.append("Risk/Regime dataset version must match schema version")
    if dataset.get("population_state") != "CLOSED_NO_PRODUCTION_RISK_REGIME_STATES":
        errors.append("Risk/Regime dataset must remain in its closed population state")
    for key in ("production_population_allowed", "automatic_ingestion_allowed", "candidate_state_storage_allowed", "synthetic_production_population_allowed", "public_risk_projection_allowed"):
        if (schema.get("population_policy") or {}).get(key) is not False:
            errors.append(f"Risk/Regime population policy must keep {key}=false")
    for key in ("canonical_mutation_allowed", "observation_mutation_allowed", "signal_mutation_allowed", "relationship_mutation_allowed", "risk_overlay_mutation_allowed", "automatic_state_promotion_allowed", "forecast_fields_allowed", "scenario_fields_allowed", "public_risk_projection_allowed"):
        if (schema.get("layer_boundary") or {}).get(key) is not False:
            errors.append(f"Risk/Regime boundary must keep {key}=false")
    if dataset["states"]:
        errors.append("closed production population gate prohibits every governed Risk/Regime state")
    errors.extend(_validate_history(schema, dataset["states"], signals, relationships, observations, evidence, canonical).errors)
    return RiskValidationReport(tuple(errors))


def risk_state_as_of(schema: dict[str, Any], revisions: list[dict[str, Any]], signals: dict[str, Any],
                     relationships: dict[str, Any], observations: dict[str, Any], evidence: dict[str, Any],
                     canonical: dict[str, Any], at_utc: str) -> dict[str, dict[str, Any]]:
    """Return each state revision effective by an explicit UTC as-of time."""
    report = validate_risk_state_history(schema, revisions, signals, relationships, observations, evidence, canonical)
    at = _utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Risk/Regime history/as-of timestamp: " + "; ".join(report.errors))
    result: dict[str, dict[str, Any]] = {}
    for row in sorted(revisions, key=lambda item: (item["state_id"], item["revision_number"])):
        if _revision_time(row) <= at:
            result[row["state_id"]] = {
                "revision_id": row["revision_id"],
                "state_class": row["state_class"],
                "current_state": row["current_state"],
                "previous_state": row["previous_state"],
                "transition_type": row["transition_type"],
                "lifecycle_state": row["lifecycle_state"],
                "review_state": row["review_state"],
            }
    return result


def risk_state_is_stale(row: dict[str, Any], observations: dict[str, dict[str, Any]], at_utc: str) -> bool:
    """Evaluate expiry deterministically at an explicit UTC time.

    This helper never uses wall-clock time.  ``STALE_AFTER`` is anchored to the
    latest explicitly linked supporting observation; fixed-date modes are
    evaluated directly from their governed deadline.
    """
    at = _utc(at_utc)
    if at is None:
        raise ValueError("at_utc must be exact UTC")
    expiry = row["expiry"]
    if expiry["mode"] == "EXPLICIT_DATE":
        return at >= _utc(expiry["expires_at_utc"])
    if expiry["mode"] == "REVIEW_REQUIRED":
        return at >= _utc(expiry["review_due_at_utc"])
    observed = [
        _utc(observations[observation_id]["observed_at_utc"])
        for observation_id in row["supporting_observation_ids"]
        if observation_id in observations and _utc(observations[observation_id].get("observed_at_utc")) is not None
    ]
    if not observed:
        raise ValueError("STALE_AFTER requires at least one linked observation")
    return at >= max(observed) + timedelta(days=expiry["stale_after_days"])


def public_risk_state_projection(schema: dict[str, Any], dataset: dict[str, Any], signals: dict[str, Any],
                                 relationships: dict[str, Any], observations: dict[str, Any],
                                 evidence: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    report = validate_risk_states(schema, dataset, signals, relationships, observations, evidence, canonical)
    if not report.ok:
        raise ValueError("invalid Risk/Regime state: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "RISK_REGIME_CONTRACT_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": dataset.get("population_state"),
            "internal_state_count": 0,
            "public_state_count": 0,
            "automatic_state_promotion": False,
            "public_risk_projection_allowed": False,
        },
        "states": [],
    }
