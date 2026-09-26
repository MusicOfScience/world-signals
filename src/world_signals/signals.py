"""Validation and closed projection for the reviewed Signal contract.

A Signal is a reviewed analytical inference over immutable Live Intelligence
observations. This module intentionally validates a closed, empty production
dataset on the current milestone while providing the stable interface and
pressure-tested rules needed for a future reviewed admission transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
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


def _validate_signal_history(
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
            for ref in evidence_refs
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

    return SignalValidationReport(tuple(errors))


def observation_digest(row: dict) -> str:
    """Pin the full immutable upstream snapshot, independent of JSON formatting."""
    value = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(value.encode()).hexdigest()


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _strings(value):
    return isinstance(value, list) and all(_text(x) for x in value)


def _preflight(schema, dataset, observations, evidence):
    """Type-check untrusted JSON before indexing, sorting, hashing or arithmetic."""
    errors = []
    if not all(isinstance(x, dict) for x in (schema, dataset, observations, evidence)):
        return ["schema and datasets must be objects"]
    try:
        json.dumps([schema, dataset, observations, evidence], allow_nan=False)
    except (TypeError, ValueError):
        return ["inputs must be finite JSON values"]
    if schema.get("version") != "0.1":
        errors.append("unsupported Signal schema version")
    for key in ("layer_boundary", "population_policy", "public_projection_policy", "controlled_vocabularies"):
        if not isinstance(schema.get(key), dict):
            errors.append(f"{key} must be an object")
    for key in ("required_signal_fields", "prohibited_fields"):
        if not _strings(schema.get(key)) or not schema[key]:
            errors.append(f"{key} must be a non-empty string list")
    for data, key, id_key in ((observations, "observations", "observation_id"), (evidence, "evidence", "evidence_id")):
        if not isinstance(data.get(key), list):
            errors.append(f"{key} must be a list")
            continue
        for row in data[key]:
            if not isinstance(row, dict) or not _text(row.get(id_key)):
                errors.append(f"{id_key} must be non-empty text")
                continue
            if key == "observations":
                if (not _strings(row.get("evidence_refs")) or not _parse_exact_utc(row.get("observed_at_utc"))
                        or not _text(row.get("verification_state"))
                        or (row.get("revision_of_observation_id") is not None and not _text(row["revision_of_observation_id"]))):
                    errors.append("invalid upstream observation evidence/time/state/revision")
            elif not _text(row.get("provider")) or not _text(row.get("evidence_class")):
                errors.append("invalid upstream evidence provider/class")
    if errors:
        return errors
    vocab = schema["controlled_vocabularies"]
    for key in ("signal_type", "direction", "magnitude", "novelty", "persistence", "trend_state", "confidence",
                "review_state", "lifecycle_state", "signal_domain", "relationship_status", "expiry_mode", "corroboration_state"):
        if not _strings(vocab.get(key)) or not vocab[key]:
            errors.append(f"invalid vocabulary {key}")
    if not isinstance(dataset.get("signals"), list):
        return errors + ["signals must be a list"]
    for row in dataset["signals"]:
        if not isinstance(row, dict):
            errors.append("Signal must be an object")
            continue
        if set(row) != set(schema["required_signal_fields"]):
            errors.append("missing/unknown Signal fields; forecast/scenario fields are prohibited")
            continue
        for key in ("signal_id", "revision_id", "title", "signal_type", "direction", "magnitude", "novelty",
                    "persistence", "trend_state", "confidence", "review_state", "lifecycle_state",
                    "supporting_rationale", "revision_reason", "latest_supporting_observation_id"):
            if not _text(row.get(key)):
                errors.append(f"{key} must be non-empty text")
        if type(row.get("revision_number")) is not int or row["revision_number"] < 1:
            errors.append("revision_number must be a positive integer")
        if row.get("previous_revision_id") is not None and not _text(row["previous_revision_id"]):
            errors.append("invalid previous_revision_id")
        for key in ("observation_ids", "evidence_refs", "contradictory_evidence_refs", "entities", "jurisdictions",
                    "regions", "domains", "falsification_conditions", "correction_review_observation_ids"):
            if not _strings(row.get(key)):
                errors.append(f"{key} must be a list of strings")
        if row.get("review_state") not in ("CANDIDATE", "UNDER_REVIEW", "ACCEPTED", "REJECTED"):
            errors.append("invalid review state")
        if row.get("lifecycle_state") not in ("UNRESOLVED", "ACTIVE", "WEAKENING", "EXPIRED", "WITHDRAWN", "SUPERSEDED"):
            errors.append("invalid lifecycle state")
        objects = {"baseline": {"description", "observation_ids"},
                   "assessment_basis": {"materiality", "novelty", "persistence", "trend", "confidence", "source_quality", "coverage_bias", "alternatives"},
                   "corroboration": {"state", "independent_observation_count", "distinct_provider_count", "rationale"},
                   "review_provenance": {"created_by", "created_at_utc", "reviewed_by", "reviewed_at_utc", "decision_basis"}}
        valid = True
        for key, fields in objects.items():
            if not isinstance(row.get(key), dict) or set(row[key]) != fields:
                errors.append(f"{key} must be an object with exactly {sorted(fields)}")
                valid = False
        if not valid:
            continue
        corr = row["corroboration"]
        if not _text(corr["state"]) or not _text(corr["rationale"]):
            errors.append("invalid corroboration state/rationale")
        for key in ("independent_observation_count", "distinct_provider_count"):
            if type(corr[key]) is not int or corr[key] < 0:
                errors.append(f"{key} must be a non-negative integer")
        if not _text(row["baseline"]["description"]) or not _strings(row["baseline"]["observation_ids"]) or not row["baseline"]["observation_ids"]:
            errors.append("baseline requires description and observation_ids")
        if any(not _text(x) for x in row["assessment_basis"].values()):
            errors.append("assessment_basis requires qualitative justifications")
        if not isinstance(row.get("observation_hashes"), dict) or any(not _text(x) for x in row["observation_hashes"].values()):
            errors.append("observation_hashes must be a digest map")
        for key in ("first_detected_at_utc",):
            if not _parse_exact_utc(row.get(key)):
                errors.append(f"invalid {key}")
        review = row["review_provenance"]
        if not _text(review["created_by"]) or not _parse_exact_utc(review["created_at_utc"]):
            errors.append("invalid assessment author/time")
        if review["reviewed_at_utc"] is not None and not _parse_exact_utc(review["reviewed_at_utc"]):
            errors.append("invalid review decision timestamp")
        expiry = row.get("expiry")
        if not isinstance(expiry, dict) or not _text(expiry.get("mode")) or not _text(expiry.get("condition")):
            errors.append("expiry requires mode and condition")
        elif expiry["mode"] == "STALE_AFTER":
            if set(expiry) != {"mode", "condition", "stale_after_days"} or type(expiry.get("stale_after_days")) is not int or not 0 < expiry["stale_after_days"] <= 36500:
                errors.append("invalid bounded stale_after_days")
        elif expiry["mode"] in ("EXPLICIT_DATE", "REVIEW_REQUIRED"):
            key = "expires_at_utc" if expiry["mode"] == "EXPLICIT_DATE" else "review_due_at_utc"
            if set(expiry) != {"mode", "condition", key} or not _parse_exact_utc(expiry.get(key)):
                errors.append("expiry requires a deterministic UTC deadline")
        else:
            errors.append("unbounded expiry is prohibited")
        for key, fields in (("transmission_relevance", {"channel", "affected_domains", "relationship_status", "rationale"}),
                            ("evidence_lineage", {"evidence_ref", "origin_ids", "basis"})):
            if not isinstance(row.get(key), list):
                errors.append(f"{key} must be a list")
                continue
            for item in row[key]:
                if not isinstance(item, dict) or set(item) != fields:
                    errors.append(f"invalid {key} fields")
                    continue
                list_key = "affected_domains" if key == "transmission_relevance" else "origin_ids"
                if not _strings(item[list_key]) or not item[list_key] or any(not _text(item[k]) for k in fields - {list_key}):
                    errors.append(f"invalid {key} values")
                if key == "transmission_relevance" and item.get("relationship_status") not in ("HYPOTHESISED_TRANSMISSION", "OBSERVED_ASSOCIATION"):
                    errors.append("reviewed causal mechanisms require the later Relationship contract")
    return errors


def _corrections(ids, observations, at):
    """CM corrections are NEW snapshots pointing to the unchanged ancestor."""
    found, affected = set(), set(ids)
    while True:
        added = {oid for oid, row in observations.items()
                 if row.get("revision_of_observation_id") in affected
                 and row["verification_state"] in {"CORRECTED", "RETRACTED"}
                 and _parse_exact_utc(row["observed_at_utc"]) <= at} - found
        if not added:
            return found
        found |= added
        affected |= added


def _deadline(row, observations):
    expiry = row["expiry"]
    if expiry["mode"] == "STALE_AFTER":
        at = _parse_exact_utc(observations[row["latest_supporting_observation_id"]]["observed_at_utc"])
        try:
            return at + timedelta(days=expiry["stale_after_days"])
        except OverflowError:
            return datetime.max.replace(tzinfo=timezone.utc)
    key = "expires_at_utc" if expiry["mode"] == "EXPLICIT_DATE" else "review_due_at_utc"
    return _parse_exact_utc(expiry[key])


def _independence(row, observations, evidence, errors):
    lineage = {}
    for item in row["evidence_lineage"]:
        ref = item["evidence_ref"]
        roots = {_normalise_provider(x) for x in item["origin_ids"]}
        if ref in lineage or len(roots) != len(item["origin_ids"]):
            errors.append("duplicate evidence lineage/root")
        if roots & {_normalise_provider(x) for x in evidence}:
            errors.append("circular lineage: origins must be ultimate sources, not evidence references")
        lineage[ref] = roots
    if set(lineage) != set(row["evidence_refs"] + row["contradictory_evidence_refs"]):
        errors.append("lineage must cover exactly supporting and contradictory evidence")
        return
    # Connected components collapse same-provider, syndicated/shared-origin and
    # identical-document reports, including transitive overlap.
    groups = []
    for ref in row["evidence_refs"]:
        item = evidence[ref]
        tokens = {("provider", _normalise_provider(item["provider"]))}
        tokens |= {("origin", x) for x in lineage[ref]}
        if _text(item.get("url")):
            tokens.add(("url", item["url"].strip().split("#")[0].rstrip("/")))
        groups.append((tokens, {ref}))
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i+1, len(groups)):
                if groups[i][0] & groups[j][0]:
                    groups[i] = (groups[i][0] | groups[j][0], groups[i][1] | groups[j][1])
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break
    # Maximum matching: one observation cannot count multiple times even when
    # it cites several independent collection origins.
    assigned = {}
    def match(index, seen):
        for oid in sorted(row["observation_ids"]):
            if oid in seen or not set(observations[oid]["evidence_refs"]) & groups[index][1]:
                continue
            seen.add(oid)
            if oid not in assigned or match(assigned[oid], seen):
                assigned[oid] = index
                return True
        return False
    count = sum(match(i, set()) for i in range(len(groups)))
    if row["corroboration"]["independent_observation_count"] != count:
        errors.append("independent_observation_count disagrees with supporting origin components")


def validate_signal_history(schema, revisions, observations_dataset, evidence_registry, *, previous_revisions=None):
    """Pressure-test proposed records, without storage or publication permission.

    A retained prior snapshot is required by any future admission transaction to
    detect historical edits; an isolated JSON snapshot cannot prove immutability.
    Existing Live validators remain responsible for the full upstream contract.
    """
    dataset = {"version": "0.1", "population_state": "CLOSED_NO_PRODUCTION_SIGNALS", "signals": revisions}
    errors = _preflight(schema, dataset, observations_dataset, evidence_registry)
    if errors:
        return SignalValidationReport(tuple(errors))
    report = _validate_signal_history(schema, dataset, observations_dataset, evidence_registry)
    if not report.ok:
        return report
    observations = {x["observation_id"]: x for x in observations_dataset["observations"]}
    evidence = {x["evidence_id"]: x for x in evidence_registry["evidence"]}
    by_revision = {r["revision_id"]: r for r in revisions}
    if previous_revisions is not None:
        if not isinstance(previous_revisions, list):
            errors.append("previous_revisions must be retained snapshots")
        else:
            for old in previous_revisions:
                if not isinstance(old, dict) or not _text(old.get("revision_id")) or by_revision.get(old["revision_id"]) != old:
                    errors.append("retained revision was removed or rewritten")
    for row in revisions:
        ids = set(row["observation_ids"])
        support = set(row["evidence_refs"])
        linked = {ref for oid in ids for ref in observations[oid]["evidence_refs"]}
        if linked != support | set(row["contradictory_evidence_refs"]):
            errors.append("every linked evidence item must be explicitly supporting or contradictory")
        if any(observations[oid]["verification_state"] == "CONFLICTING_REPORTS" for oid in ids) and not row["contradictory_evidence_refs"]:
            errors.append("conflicting upstream observations require explicit contrary evidence")
        if not set(row["baseline"]["observation_ids"]) <= ids:
            errors.append("baseline observation_ids must be linked")
        if set(row["observation_hashes"]) != ids or any(row["observation_hashes"].get(oid) != observation_digest(observations[oid]) for oid in ids):
            errors.append("immutable observation snapshot hash mismatch")
        review = row["review_provenance"]
        created = _parse_exact_utc(review["created_at_utc"])
        reviewed = _parse_exact_utc(review["reviewed_at_utc"])
        times = [_parse_exact_utc(observations[oid]["observed_at_utc"]) for oid in ids]
        first = _parse_exact_utc(row["first_detected_at_utc"])
        if first > created or any(t > created for t in times):
            errors.append("future evidence cannot inform an earlier assessment")
        supporting_ids = {oid for oid in ids if set(observations[oid]["evidence_refs"]) & support}
        latest = row["latest_supporting_observation_id"]
        if latest not in supporting_ids or _parse_exact_utc(observations[latest]["observed_at_utc"]) != max(_parse_exact_utc(observations[oid]["observed_at_utc"]) for oid in supporting_ids):
            errors.append("latest_supporting_observation_id must be the latest support")
            continue
        if row["persistence"] == "PERSISTENT" and (len(support) < 2 or len({_parse_exact_utc(observations[oid]["observed_at_utc"]) for oid in supporting_ids}) < 2):
            errors.append("PERSISTENT requires support at multiple observation times")
        for ref in support | set(row["contradictory_evidence_refs"]):
            if evidence[ref]["evidence_class"] not in {"PRIMARY_OFFICIAL", "REPUTABLE_NEWSWIRE", "REPUTABLE_MEDIA", "MARKET_DATA_PROVIDER", "ACADEMIC_OR_INSTITUTIONAL"}:
                errors.append("unsupported evidence class; model-generated text is not evidence")
            roles = evidence[ref].get("roles")
            factual_roles = {"FACTUAL_OBSERVATION", "SOURCE_CONFIRMATION", "MARKET_OBSERVATION", "CORRECTION_OR_REVISION"}
            if ref in support and (not _strings(roles) or not set(roles) & factual_roles):
                errors.append("support requires factual evidence roles; context-only text cannot corroborate")
            publication = evidence[ref].get("publication_time")
            if isinstance(publication, dict):
                published = _parse_exact_utc(publication.get("published_at_utc"))
                civil = publication.get("published_date")
                if (published and published > created) or (isinstance(civil, str) and civil > created.date().isoformat()):
                    errors.append("future publication cannot inform an earlier assessment")
        _independence(row, observations, evidence, errors)
        if row["review_state"] in {"ACCEPTED", "REJECTED"}:
            if not _text(review["reviewed_by"]) or not _text(review["decision_basis"]) or reviewed is None or reviewed < created:
                errors.append("decision requires reviewer, non-backdated UTC timestamp and reason")
        elif any(review[k] is not None for k in ("reviewed_by", "reviewed_at_utc", "decision_basis")):
            errors.append("unresolved review must not claim a completed decision")
        if row["review_state"] == "ACCEPTED" and row["lifecycle_state"] == "UNRESOLVED":
            errors.append("accepted Signal requires a resolved lifecycle")
        acknowledged = set(row["correction_review_observation_ids"])
        if len(acknowledged) != len(row["correction_review_observation_ids"]) or not acknowledged <= ids or any(observations[oid]["verification_state"] not in {"CORRECTED", "RETRACTED"} for oid in acknowledged & ids):
            errors.append("correction review must reference linked CM correction/retraction snapshots")
        previous = by_revision.get(row["previous_revision_id"])
        if previous:
            old = previous["review_provenance"]
            if created <= _parse_exact_utc(old["reviewed_at_utc"] or old["created_at_utc"]):
                errors.append("revision time must strictly advance beyond prior decision")
            if row["first_detected_at_utc"] != previous["first_detected_at_utc"]:
                errors.append("first detection must remain stable")
            transitions = {"CANDIDATE": {"CANDIDATE", "UNDER_REVIEW"}, "UNDER_REVIEW": {"UNDER_REVIEW", "ACCEPTED", "REJECTED"},
                           "ACCEPTED": {"ACCEPTED", "UNDER_REVIEW"}, "REJECTED": {"UNDER_REVIEW"}}
            if row["review_state"] not in transitions[previous["review_state"]]:
                errors.append("invalid review transition")
            if previous["lifecycle_state"] in {"EXPIRED", "WITHDRAWN", "SUPERSEDED"} and row["lifecycle_state"] != "UNRESOLVED":
                errors.append("terminal lifecycle requires reopening review before reactivation")
        elif first < min(times):
            errors.append("initial first detection cannot predate all linked observations")
        if row["lifecycle_state"] in {"ACTIVE", "WEAKENING"} and reviewed:
            if _deadline(row, observations) <= reviewed:
                errors.append("active decision is stale/expired at review time")
            dependencies = ids | (set(previous["observation_ids"]) if previous else set())
            corrections = _corrections(dependencies, observations, reviewed)
            if corrections - acknowledged:
                errors.append("known observation corrections require explicit Signal review")
            ancestors = {observations[oid].get("revision_of_observation_id") for oid in corrections}
            if supporting_ids & ancestors or any(observations[oid]["verification_state"] == "RETRACTED" for oid in supporting_ids):
                errors.append("corrected/retracted ancestor must not remain active support")
    return SignalValidationReport(tuple(errors))


def validate_signals(schema, signals_dataset, observations_dataset, evidence_registry):
    """Production admission: no fixture switch or alternate population mode."""
    errors = _preflight(schema, signals_dataset, observations_dataset, evidence_registry)
    if errors:
        return SignalValidationReport(tuple(errors))
    if signals_dataset["signals"]:
        errors.append("closed production population gate prohibits every Signal revision")
    errors.extend(_validate_signal_history(schema, signals_dataset, observations_dataset, evidence_registry).errors)
    return SignalValidationReport(tuple(errors))


def signal_state_as_of(schema, revisions, observations_dataset, evidence_registry, at_utc):
    """Internal deterministic state inspection. Never changes stored history."""
    report = validate_signal_history(schema, revisions, observations_dataset, evidence_registry)
    at = _parse_exact_utc(at_utc)
    if not report.ok or at is None:
        raise ValueError("invalid Signal history/as-of timestamp: " + "; ".join(report.errors))
    observations = {r["observation_id"]: r for r in observations_dataset["observations"]}
    heads = {}
    for row in sorted(revisions, key=lambda r: (r["signal_id"], r["revision_number"])):
        review = row["review_provenance"]
        if _parse_exact_utc(review["reviewed_at_utc"] or review["created_at_utc"]) <= at:
            heads[row["signal_id"]] = row
    result = {}
    for sid, row in heads.items():
        state = row["lifecycle_state"]
        corrections = sorted(_corrections(set(row["observation_ids"]), observations, at) - set(row["correction_review_observation_ids"]))
        if state in {"ACTIVE", "WEAKENING"}:
            if corrections:
                state = "REVIEW_REQUIRED"
            elif _deadline(row, observations) <= at:
                state = "REVIEW_REQUIRED" if row["expiry"]["mode"] == "REVIEW_REQUIRED" else "STALE"
        result[sid] = {"revision_id": row["revision_id"], "effective_state": state, "correction_observation_ids": corrections}
    return result


def observation_signal_dependencies(revisions):
    """Reverse index of validated immutable history, including retired dependencies."""
    result = {}
    for row in revisions:
        for oid in row["observation_ids"]:
            result.setdefault(oid, set()).add(row["signal_id"])
    return {oid: sorted(ids) for oid, ids in sorted(result.items())}


def public_signal_projection(
    schema: dict[str, Any],
    signals_dataset: dict[str, Any],
    observations_dataset: dict[str, Any],
    evidence_registry: dict[str, Any],
) -> dict[str, Any]:
    report = validate_signals(schema, signals_dataset, observations_dataset, evidence_registry)
    if not report.ok:
        raise ValueError("invalid Signal state: " + "; ".join(report.errors))
    return {
        "metadata": {
            "projection_type": "SIGNAL_CONTRACT_CLOSED_PROJECTION",
            "schema_version": schema.get("version"),
            "population_state": signals_dataset.get("population_state"),
            "internal_signal_count": 0,
            "public_signal_count": 0,
            "observation_dataset_version": observations_dataset.get("version"),
            "evidence_dataset_version": evidence_registry.get("version"),
            "automatic_signal_promotion": False,
            "public_signal_projection_allowed": False,
        },
        "signals": [],
    }
