"""Validation and closed projection for the reviewed Signal contract.

A Signal is a reviewed analytical inference over immutable Live Intelligence
observations. This module intentionally validates a closed, empty production
dataset on the current milestone while providing the stable interface and
pressure-tested rules needed for a future reviewed admission transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class SignalValidationReport:
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse_exact_utc(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        return None
    return parsed.astimezone(timezone.utc)


def _normalise_provider(raw: Any) -> str:
    return " ".join(str(raw or "").strip().casefold().split())


def _all_keys(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            found.add(str(key))
            found.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            found.update(_all_keys(child))
    return found


def _string_list(value: Any, field: str, signal_id: str, errors: list[str]) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{signal_id}: {field} must be a list of non-empty strings")
        return []
    return [item.strip() for item in value]


def _validate_transmission(
    signal: dict[str, Any],
    allowed_domains: set[str],
    allowed_relationships: set[str],
    errors: list[str],
) -> None:
    signal_id = str(signal.get("signal_id") or "<missing-signal-id>")
    rows = signal.get("transmission_relevance")
    if not isinstance(rows, list):
        errors.append(f"{signal_id}: transmission_relevance must be a list")
        return
    for index, row in enumerate(rows):
        prefix = f"{signal_id}: transmission_relevance[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{prefix} must be an object")
            continue
        if not isinstance(row.get("channel"), str) or not row["channel"].strip():
            errors.append(f"{prefix}.channel is required")
        affected = row.get("affected_domains")
        if not isinstance(affected, list) or not affected or any(item not in allowed_domains for item in affected):
            errors.append(f"{prefix}.affected_domains must contain controlled domains")
        if row.get("relationship_status") not in allowed_relationships:
            errors.append(f"{prefix}.relationship_status is not controlled")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            errors.append(f"{prefix}.rationale is required")


def _validate_expiry(signal: dict[str, Any], allowed_modes: set[str], errors: list[str]) -> None:
    signal_id = str(signal.get("signal_id") or "<missing-signal-id>")
    expiry = signal.get("expiry")
    if not isinstance(expiry, dict):
        errors.append(f"{signal_id}: expiry must be an object")
        return
    mode = expiry.get("mode")
    if mode not in allowed_modes:
        errors.append(f"{signal_id}: invalid expiry mode {mode}")
        return
    if mode == "STALE_AFTER":
        if not isinstance(expiry.get("stale_after_days"), int) or expiry["stale_after_days"] <= 0:
            errors.append(f"{signal_id}: STALE_AFTER requires positive stale_after_days")
    elif mode == "EXPLICIT_DATE":
        if _parse_exact_utc(expiry.get("expires_at_utc")) is None:
            errors.append(f"{signal_id}: EXPLICIT_DATE requires exact expires_at_utc")
    elif mode == "REVIEW_REQUIRED":
        if not isinstance(expiry.get("condition"), str) or not expiry["condition"].strip():
            errors.append(f"{signal_id}: REVIEW_REQUIRED requires condition")


def validate_signals(
    schema: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
) -> SignalValidationReport:
    errors: list[str] = []
    if schema.get("architecture_position") != "SIGNALS":
        errors.append("Signal schema architecture_position must be SIGNALS")
    boundary = schema.get("layer_boundary") or {}
    for field in (
        "canonical_mutation_allowed",
        "observation_mutation_allowed",
        "source_monitor_mutation_allowed",
        "review_candidate_promotion_allowed",
        "automatic_signal_promotion_allowed",
        "relationship_assertion_allowed",
        "forecast_fields_allowed",
        "public_signal_projection_allowed",
    ):
        if boundary.get(field) is not False:
            errors.append(f"Signal boundary must keep {field}=false")

    version = schema.get("version")
    if signals_dataset.get("version") != version:
        errors.append("Signal dataset version must match schema version")
    if signals_dataset.get("population_state") != "CLOSED_NO_PRODUCTION_SIGNALS":
        errors.append("Signal dataset must remain in the closed population state")
    population = schema.get("population_policy") or {}
    for field in ("production_population_allowed", "automatic_ingestion_allowed", "candidate_signal_storage_allowed", "public_signal_projection_allowed", "synthetic_production_population_allowed"):
        if population.get(field) is not False:
            errors.append(f"Signal population policy must keep {field}=false")
    public_policy = schema.get("public_projection_policy") or {}
    if public_policy.get("signal_projection_allowed") is not False:
        errors.append("Signal public projection policy must keep signal_projection_allowed=false")

    observations = observations_dataset.get("observations") or []
    evidence = evidence_registry.get("evidence") or []
    observation_by_id: dict[str, dict[str, Any]] = {}
    evidence_by_id: dict[str, dict[str, Any]] = {}
    for row in observations:
        if not isinstance(row, dict):
            errors.append("observation rows must be objects")
            continue
        observation_id = row.get("observation_id")
        if observation_id in observation_by_id:
            errors.append(f"duplicate upstream observation_id {observation_id}")
        elif observation_id:
            observation_by_id[observation_id] = row
    for row in evidence:
        if not isinstance(row, dict):
            errors.append("evidence rows must be objects")
            continue
        evidence_id = row.get("evidence_id")
        if evidence_id in evidence_by_id:
            errors.append(f"duplicate upstream evidence_id {evidence_id}")
        elif evidence_id:
            evidence_by_id[evidence_id] = row

    vocab = schema.get("controlled_vocabularies") or {}
    allowed_domains = set(vocab.get("signal_domain") or [])
    allowed_relationships = set(vocab.get("relationship_status") or [])
    required = set(schema.get("required_signal_fields") or [])
    prohibited = set(schema.get("prohibited_fields") or [])
    signal_rows = signals_dataset.get("signals")
    if not isinstance(signal_rows, list):
        errors.append("signals must be a list")
        signal_rows = []

    revision_ids: set[str] = set()
    revisions_by_signal: dict[str, list[dict[str, Any]]] = {}
    for signal in signal_rows:
        if not isinstance(signal, dict):
            errors.append("signal rows must be objects")
            continue
        signal_id = str(signal.get("signal_id") or "<missing-signal-id>")
        missing = sorted(field for field in required if field not in signal)
        if missing:
            errors.append(f"{signal_id}: missing signal fields {missing}")
        revision_id = signal.get("revision_id")
        if not isinstance(revision_id, str) or not revision_id.strip():
            errors.append(f"{signal_id}: revision_id is required")
        elif revision_id in revision_ids:
            errors.append(f"duplicate signal revision_id {revision_id}")
        else:
            revision_ids.add(revision_id)
        revisions_by_signal.setdefault(signal_id, []).append(signal)

        if not isinstance(signal.get("revision_number"), int) or signal["revision_number"] <= 0:
            errors.append(f"{signal_id}: revision_number must be a positive integer")
        if not isinstance(signal.get("title"), str) or not signal["title"].strip():
            errors.append(f"{signal_id}: title is required")

        if signal.get("signal_type") not in set(vocab.get("signal_type") or []):
            errors.append(f"{signal_id}: invalid signal_type")
        for field in ("direction", "magnitude", "novelty", "persistence", "trend_state", "confidence", "review_state", "lifecycle_state"):
            if signal.get(field) not in set(vocab.get(field if field != "review_state" else "review_state") or []):
                errors.append(f"{signal_id}: invalid {field}")

        observation_ids = signal.get("observation_ids")
        if not isinstance(observation_ids, list) or not observation_ids:
            errors.append(f"{signal_id}: observation_ids must be a non-empty list")
            observation_ids = []
        else:
            invalid_observation_ids = [item for item in observation_ids if not isinstance(item, str) or not item.strip()]
            if invalid_observation_ids:
                errors.append(f"{signal_id}: observation_ids must contain non-empty strings")
                observation_ids = [item for item in observation_ids if isinstance(item, str) and item.strip()]
            if len(observation_ids) != len(set(observation_ids)):
                errors.append(f"{signal_id}: duplicate observation_ids cannot increase corroboration")
        for observation_id in observation_ids:
            if observation_id not in observation_by_id:
                errors.append(f"{signal_id}: unknown observation_id {observation_id}")

        evidence_refs = signal.get("evidence_refs")
        if not isinstance(evidence_refs, list) or not evidence_refs:
            errors.append(f"{signal_id}: evidence_refs must be a non-empty list")
            evidence_refs = []
        else:
            invalid_evidence_refs = [item for item in evidence_refs if not isinstance(item, str) or not item.strip()]
            if invalid_evidence_refs:
                errors.append(f"{signal_id}: evidence_refs must contain non-empty strings")
                evidence_refs = [item for item in evidence_refs if isinstance(item, str) and item.strip()]
            if len(evidence_refs) != len(set(evidence_refs)):
                errors.append(f"{signal_id}: duplicate evidence_refs")
        linked_evidence_refs = {
            ref
            for observation_id in observation_ids
            for ref in (observation_by_id.get(observation_id, {}).get("evidence_refs") or [])
            if isinstance(ref, str) and ref.strip()
        }
        for ref in evidence_refs:
            if ref not in evidence_by_id:
                errors.append(f"{signal_id}: unknown evidence_ref {ref}")
            elif ref not in linked_evidence_refs:
                errors.append(f"{signal_id}: evidence_ref {ref} is not traceable through linked observations")

        contradictions = signal.get("contradictory_evidence_refs")
        if not isinstance(contradictions, list):
            errors.append(f"{signal_id}: contradictory_evidence_refs must be a list")
            contradictions = []
        else:
            invalid_contradictions = [item for item in contradictions if not isinstance(item, str) or not item.strip()]
            if invalid_contradictions:
                errors.append(f"{signal_id}: contradictory_evidence_refs must contain non-empty strings")
                contradictions = [item for item in contradictions if isinstance(item, str) and item.strip()]
            if len(contradictions) != len(set(contradictions)):
                errors.append(f"{signal_id}: duplicate contradictory_evidence_refs")
        corroboration = signal.get("corroboration")
        if not isinstance(corroboration, dict):
            errors.append(f"{signal_id}: corroboration must be an object")
            corroboration = {}
        for ref in contradictions:
            if ref not in evidence_by_id:
                errors.append(f"{signal_id}: unknown contradictory evidence_ref {ref}")
            elif ref not in linked_evidence_refs:
                errors.append(f"{signal_id}: contradictory evidence_ref {ref} is not traceable through linked observations")
            if ref in evidence_refs:
                errors.append(f"{signal_id}: evidence cannot be both supporting and contradictory")
        if contradictions and corroboration.get("state") != "CONFLICTED":
            errors.append(f"{signal_id}: contradictory evidence requires CONFLICTED corroboration state")
        if corroboration.get("state") == "CONFLICTED" and not contradictions:
            errors.append(f"{signal_id}: CONFLICTED corroboration requires contradictory evidence")

        for field in ("entities", "jurisdictions", "regions"):
            _string_list(signal.get(field), field, signal_id, errors)
        domains = _string_list(signal.get("domains"), "domains", signal_id, errors)
        if any(domain not in allowed_domains for domain in domains):
            errors.append(f"{signal_id}: domains contain uncontrolled values")

        state = corroboration.get("state")
        if state not in set(vocab.get("corroboration_state") or []):
            errors.append(f"{signal_id}: invalid corroboration state")
        linked_providers = {
            _normalise_provider(evidence_by_id[ref].get("provider"))
            for ref in linked_evidence_refs
            if ref in evidence_by_id and _normalise_provider(evidence_by_id[ref].get("provider"))
        }
        distinct_providers = corroboration.get("distinct_provider_count")
        independent_count = corroboration.get("independent_observation_count")
        if not isinstance(distinct_providers, int) or distinct_providers < 0:
            errors.append(f"{signal_id}: distinct_provider_count must be a non-negative integer")
        elif distinct_providers != len(linked_providers):
            errors.append(f"{signal_id}: distinct_provider_count does not match evidence providers")
        if not isinstance(independent_count, int) or independent_count < 0:
            errors.append(f"{signal_id}: independent_observation_count must be a non-negative integer")
        elif independent_count > min(len(set(observation_ids)), len(linked_providers)):
            errors.append(f"{signal_id}: independent corroboration exceeds distinct observations/providers")
        if state == "INDEPENDENT" and (independent_count or 0) < 2:
            errors.append(f"{signal_id}: INDEPENDENT corroboration requires two independent observations")
        if state == "INDEPENDENT" and (distinct_providers or 0) < 2:
            errors.append(f"{signal_id}: INDEPENDENT corroboration requires two providers")

        latest_id = signal.get("latest_supporting_observation_id")
        if latest_id not in observation_ids:
            errors.append(f"{signal_id}: latest_supporting_observation_id must be linked")
        if _parse_exact_utc(signal.get("first_detected_at_utc")) is None:
            errors.append(f"{signal_id}: first_detected_at_utc must be exact UTC")
        rationale = signal.get("supporting_rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{signal_id}: supporting_rationale is required")
        falsifiers = _string_list(signal.get("falsification_conditions"), "falsification_conditions", signal_id, errors)
        if not falsifiers:
            errors.append(f"{signal_id}: at least one falsification condition is required")
        _validate_transmission(signal, allowed_domains, allowed_relationships, errors)
        _validate_expiry(signal, set(vocab.get("expiry_mode") or []), errors)

        provenance = signal.get("review_provenance")
        if not isinstance(provenance, dict):
            errors.append(f"{signal_id}: review_provenance must be an object")
        else:
            if not isinstance(provenance.get("created_by"), str) or not provenance["created_by"].strip():
                errors.append(f"{signal_id}: review_provenance.created_by is required")
            if _parse_exact_utc(provenance.get("created_at_utc")) is None:
                errors.append(f"{signal_id}: review_provenance.created_at_utc must be exact UTC")
            if signal.get("review_state") == "ACCEPTED":
                if not isinstance(provenance.get("reviewed_by"), str) or not provenance["reviewed_by"].strip():
                    errors.append(f"{signal_id}: accepted Signal requires reviewed_by")
                if not isinstance(provenance.get("decision_basis"), str) or not provenance["decision_basis"].strip():
                    errors.append(f"{signal_id}: accepted Signal requires decision_basis")

        review_state = signal.get("review_state")
        lifecycle_state = signal.get("lifecycle_state")
        if review_state in {"CANDIDATE", "UNDER_REVIEW"} and lifecycle_state != "UNRESOLVED":
            errors.append(f"{signal_id}: unaccepted Signal must be UNRESOLVED")
        if review_state == "REJECTED" and lifecycle_state != "WITHDRAWN":
            errors.append(f"{signal_id}: rejected Signal must be WITHDRAWN")
        if lifecycle_state in {"EXPIRED", "SUPERSEDED", "WITHDRAWN"} and review_state == "ACCEPTED" and not signal.get("supporting_rationale"):
            errors.append(f"{signal_id}: non-active accepted Signal requires preserved rationale")

        forbidden = prohibited.intersection(_all_keys(signal))
        if forbidden:
            errors.append(f"{signal_id}: forecast/scenario fields are prohibited: {sorted(forbidden)}")

    for signal_id, revisions in revisions_by_signal.items():
        ordered = sorted(revisions, key=lambda row: row.get("revision_number", 0))
        expected = list(range(1, len(ordered) + 1))
        actual = [row.get("revision_number") for row in ordered]
        if actual != expected:
            errors.append(f"{signal_id}: revision numbers must be contiguous from 1")
        for index, row in enumerate(ordered):
            if index == 0:
                if row.get("previous_revision_id") is not None:
                    errors.append(f"{signal_id}: first revision cannot have previous_revision_id")
            elif row.get("previous_revision_id") != ordered[index - 1].get("revision_id"):
                errors.append(f"{signal_id}: revision history does not preserve its immediate predecessor")

        latest = ordered[-1]
        latest_observations = [
            observation_by_id.get(ref, {})
            for ref in latest.get("observation_ids") or []
            if isinstance(ref, str)
        ]
        corrected = [row.get("observation_id") for row in latest_observations if row.get("verification_state") in {"CORRECTED", "RETRACTED"}]
        if corrected and latest.get("lifecycle_state") in {"ACTIVE", "WEAKENING"}:
            errors.append(f"{signal_id}: corrected/retracted observations require explicit Signal review before active use")

    return SignalValidationReport(tuple(errors))


def public_signal_projection(
    schema: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
) -> dict[str, Any]:
    report = validate_signals(schema, signals_dataset, observations_dataset, evidence_registry)
    if not report.ok:
        raise ValueError("invalid Signal state: " + "; ".join(report.errors))
    allowed = (schema.get("public_projection_policy") or {}).get("signal_projection_allowed") is True
    signals = signals_dataset.get("signals") or []
    public = [
        row
        for row in signals
        if row.get("review_state") == "ACCEPTED"
        and row.get("lifecycle_state") in {"ACTIVE", "WEAKENING"}
    ] if allowed else []
    return {
        "metadata": {
            "projection_type": "SIGNAL_CONTRACT_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": signals_dataset.get("population_state"),
            "internal_signal_count": len(signals),
            "public_signal_count": len(public),
            "observation_dataset_version": observations_dataset.get("version"),
            "evidence_dataset_version": evidence_registry.get("version"),
            "automatic_signal_promotion": False,
            "public_signal_projection_allowed": allowed,
        },
        "signals": public,
    }
