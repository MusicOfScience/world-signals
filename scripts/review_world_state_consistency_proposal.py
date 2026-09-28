#!/usr/bin/env python3
"""Review one retained World State consistency proposal.

This command records an explicit human review transaction under
``data/world_state_audit/``.  It is deliberately not a production admission
writer: acceptance is limited to the read-boundary consistency scope, has no
write targets, and cannot enable public projection.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from retain_world_state_consistency_proposal import (  # noqa: E402
    _manifest_headers,
    validate_retained_package,
)
from world_signals.world_state_read import (  # noqa: E402
    WorldStateReadError,
    read_world_state,
    semantic_fingerprint,
)


AUDIT_DIR = ROOT / "data/world_state_audit"
DEFAULT_PROPOSAL = AUDIT_DIR / "CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_PENDING.json"
DEFAULT_REVIEWED_AT_UTC = "2026-09-27T06:39:19Z"
EXPECTED_AS_OF_UTC = "2026-09-27T04:39:04Z"
EXPECTED_PROPOSAL_FINGERPRINT = "8d5161ca7e3fccdaf3a8d765a0c27bccb6340b465f61d6f8931f01488170bea2"
EXPECTED_SOURCE_MANIFEST_SHA256 = "10f7657331e1eee930a82dfb0ecf01c66e6e55420c87f95d8cf1c65bd9f54b8a"
EXPECTED_RETAINED_MANIFEST_SHA256 = "3524b2eb8d8d843434ac83b2ce8b70b1ccc3f1f35828e1cca38ce0035f68e3bd"
DECISION_SCOPE = "READ_BOUNDARY_CONSISTENCY_ONLY"
TRANSACTION_TYPE = "WORLD_STATE_SYNTHESIS_REVIEW"
EXPECTED_FORECAST_IDS = {
    "WS-FP-BOC-20261028",
    "WS-FP-ECB-20261029",
    "WS-FP-FED-20261028",
    "WS-FP-RBA-20261103",
}


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_compact_json(value).encode("utf-8")).hexdigest()


def _parse_utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise WorldStateReadError(f"{field} must be an exact UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise WorldStateReadError(f"{field} is not valid UTC") from exc
    if parsed.tzinfo != timezone.utc:
        raise WorldStateReadError(f"{field} must be UTC")
    return parsed


def _proposal_body(proposal: dict[str, Any]) -> dict[str, Any]:
    body = deepcopy(proposal)
    for key in ("source_manifest", "source_manifest_sha256", "semantic_fingerprint", "proposal_id"):
        body.pop(key, None)
    # The retained Step 4 package predates the explicit PASS status field in
    # the mutation proof.  Status is execution metadata; the before/after
    # hashes remain the semantic proof and must compare exactly.
    # Mutation hashes prove the read was non-mutating at the time it ran, but
    # are not part of the retained proposal's semantic content.  Later
    # governed admissions may legitimately change the current repository file
    # hashes without changing what the earlier cutoff selected.
    body.pop("mutation_check", None)
    return body


def _criterion(status: str, disposition: str, basis: str) -> dict[str, str]:
    return {"status": status, "disposition": disposition, "basis": basis}


def _fresh_read_matches(package: dict[str, Any]) -> list[str]:
    """Re-read current governed inputs and compare the retained semantic body."""
    errors: list[str] = []
    try:
        fresh = read_world_state(package["read_request"])
    except (WorldStateReadError, OSError, json.JSONDecodeError) as exc:
        return [f"current governed read failed: {exc}"]

    retained_body = _proposal_body(package.get("proposal", {}))
    if _proposal_body(fresh) != retained_body:
        errors.append("retained proposal body differs from the current governed read")
    fingerprint_input = deepcopy(fresh)
    # Reproduce the retained semantic fingerprint with the retained
    # mutation-proof object.  Selected objects and their manifest remain exact
    # and are checked independently below; only the repository-wide before /
    # after hashes may legitimately differ after later admissions.
    fingerprint_input["mutation_check"] = deepcopy(package["proposal"].get("mutation_check", {}))
    if semantic_fingerprint(fingerprint_input) != EXPECTED_PROPOSAL_FINGERPRINT:
        errors.append("current governed read semantic fingerprint differs from expected")
    if fresh.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST_SHA256:
        errors.append("current governed read source manifest differs from expected")
    headers = _manifest_headers(fresh.get("source_manifest", []))
    if headers != package.get("source_manifest"):
        errors.append("retained hash-only manifest differs from the current governed read")
    if _sha256(headers) != EXPECTED_RETAINED_MANIFEST_SHA256:
        errors.append("current retained manifest fingerprint differs from expected")
    if fresh.get("mutation_check", {}).get("status") != "PASS":
        errors.append("current governed read mutation proof is not PASS")
    return errors


def _review_invariant_errors(package: dict[str, Any]) -> list[str]:
    errors = list(validate_retained_package(package))
    if package.get("package_type") != "WORLD_STATE_CONSISTENCY_PROPOSAL":
        errors.append("unexpected retained package type")
    if package.get("semantic_proposal_fingerprint") != EXPECTED_PROPOSAL_FINGERPRINT:
        errors.append("proposal semantic fingerprint does not match the approved review target")
    if package.get("source_manifest_sha256") != EXPECTED_SOURCE_MANIFEST_SHA256:
        errors.append("source manifest SHA-256 does not match the approved review target")
    if package.get("retained_manifest_sha256") != EXPECTED_RETAINED_MANIFEST_SHA256:
        errors.append("retained manifest SHA-256 does not match the approved review target")
    request = package.get("read_request", {})
    if request.get("as_of_utc") != EXPECTED_AS_OF_UTC:
        errors.append("proposal cutoff does not match the approved review target")
    if package.get("public_projection_permitted") is not False:
        errors.append("public projection is not closed")
    if package.get("no_write_targets") is not True or package.get("review_state", {}).get("write_targets") != []:
        errors.append("proposal does not have an empty write-target boundary")
    if package.get("production_world_state") is not False:
        errors.append("proposal is marked as production World State")
    if package.get("review_state", {}).get("decision") != "REVIEW_PENDING":
        errors.append("proposal is not still review pending")
    if package.get("mutation_proof", {}).get("status") != "PASS":
        errors.append("retained mutation proof is not PASS")
    if package.get("mutation_proof", {}).get("before") != package.get("mutation_proof", {}).get("after"):
        errors.append("retained before/after governed hashes differ")

    proposal = package.get("proposal", {})
    if proposal.get("evaluation", {}).get("evaluation_state") != "NO_SAMPLE":
        errors.append("Evaluation is not NO_SAMPLE")
    if proposal.get("production_populations") != {
        "relationships": 0,
        "risks_regimes": 0,
        "scenarios": 0,
        "outcomes": 0,
    }:
        errors.append("production empty-layer populations changed")
    for field in (
        "actors", "implementation_claims", "dimension_assessments", "hypotheses",
        "transmission_edges", "negative_evidence",
    ):
        if proposal.get(field) != []:
            errors.append(f"proposal contains unsupported analytical field {field}")
    if proposal.get("relationships") != []:
        errors.append("proposal contains relationship edges")
    if "CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED" not in {
        row.get("code") for row in proposal.get("limitations", [])
    }:
        errors.append("Canonical historical limitation is missing")

    refs = proposal.get("forecast_outcome_references")
    if not isinstance(refs, list) or {row.get("forecast_id") for row in refs} != EXPECTED_FORECAST_IDS:
        errors.append("Forecast reference set does not match the retained four Forecasts")
    for row in refs or []:
        try:
            cutoff = _parse_utc(row["information_cutoff_at_utc"], "Forecast information cutoff")
            issue = _parse_utc(row["issued_at_utc"], "Forecast issued_at_utc")
            proposal_cutoff = _parse_utc(EXPECTED_AS_OF_UTC, "proposal cutoff")
        except (KeyError, WorldStateReadError) as exc:
            errors.append(f"invalid Forecast cutoff metadata: {exc}")
            continue
        if cutoff > proposal_cutoff:
            errors.append(f"Forecast {row.get('forecast_id')} uses future information")
        if issue > proposal_cutoff:
            errors.append(f"Forecast {row.get('forecast_id')} was issued after the proposal cutoff")
        if not row.get("issuance_id") or not row.get("revision_id") or not row.get("resolution"):
            errors.append(f"Forecast {row.get('forecast_id')} lacks issuance or resolution identity")
        if row.get("outcome_revision_ids") != []:
            errors.append(f"Forecast {row.get('forecast_id')} has an Outcome before eligibility")
    if proposal.get("selected_inputs", {}).get("outcomes") != []:
        errors.append("future Outcome is selected")
    return errors


def validate_review_candidate(package: dict[str, Any], *, verify_current_inputs: bool = True) -> list[str]:
    """Return fail-closed errors for the exact Step 4 review target."""
    errors = _review_invariant_errors(package)
    if verify_current_inputs and not errors:
        errors.extend(_fresh_read_matches(package))
    return errors


def build_review_transaction(
    package: dict[str, Any],
    *,
    decision: str,
    reviewed_at_utc: str,
    verify_current_inputs: bool = True,
) -> dict[str, Any]:
    """Build a deterministic review record from an explicit human decision."""
    if not decision:
        raise WorldStateReadError("an explicit review decision is required; no default acceptance exists")
    if decision != "ACCEPTED":
        raise WorldStateReadError("Step 5 accepts only the explicit READ_BOUNDARY_CONSISTENCY_ONLY decision")
    _parse_utc(reviewed_at_utc, "reviewed_at_utc")
    errors = validate_review_candidate(package, verify_current_inputs=verify_current_inputs)
    if errors:
        raise WorldStateReadError("review candidate failed closed: " + "; ".join(errors))

    proposal = package["proposal"]
    empty = {
        "relationships": 0,
        "risks_regimes": 0,
        "scenarios": 0,
        "outcomes": 0,
        "actors": len(proposal["actors"]),
        "implementation_claims": len(proposal["implementation_claims"]),
        "dimension_assessments": len(proposal["dimension_assessments"]),
        "hypotheses": len(proposal["hypotheses"]),
        "transmission_edges": len(proposal["transmission_edges"]),
        "negative_evidence": len(proposal["negative_evidence"]),
    }
    criterion_results = {
        "authority_interpretation": _criterion("PASS", "NO_CLAIMS_TO_REVIEW", "actors=[]; no Actor Registry or authority claim was created."),
        "implementation_state": _criterion("PASS", "NO_IMPLEMENTATION_CLAIMS", "All SAID/DECIDED/AUTHORISED/IMPLEMENTED/OBSERVED claim populations are empty."),
        "contradictions": _criterion("PASS", "UPSTREAM_CONTRACTS_PRESERVED", "No proposal-level analytical claim suppresses contradiction-bearing upstream references; evidence counts are not confidence."),
        "negative_evidence": _criterion("PASS", "EMPTY_RESULT_CORRECT", "negative_evidence=[]; absence, unqueried sources and source failure were not promoted."),
        "market_rights": _criterion("PASS", "NO_NEW_MARKET_CLAIM", "No market feed or causal claim was introduced; existing Analysis rights remain upstream."),
        "graph_classes": _criterion("PASS", "EMPTY_RESULT_CORRECT", "relationships=0 and transmission_edges=0; no proximity or transitive edge was generated."),
        "forecast_cutoff_integrity": _criterion("PASS", "FOUR_ISSUANCES_PRESERVED", "All four Forecast identities, revisions, cutoffs, resolution rules and empty Outcome references are retained."),
        "evaluation": _criterion("PASS", "NO_SAMPLE_ACCEPTED", "Outcomes=0 and Evaluation remains NO_SAMPLE; no calibration denominator was manufactured."),
        "empty_layer_integrity": _criterion("PASS", "GOVERNED_EMPTY_RESULTS_ACCEPTED", json.dumps(empty, sort_keys=True)),
        "canonical_limitation": _criterion("PASS", "LIMITATION_RETAINED", "CANONICAL_HISTORICAL_AS_OF_UNSUPPORTED remains explicit; current context is not historical truth."),
        "mutation_protection": _criterion("PASS", "BEFORE_EQUALS_AFTER", "The retained governed-input before/after hashes are identical."),
        "manifest_integrity": _criterion("PASS", "EXACT_FINGERPRINTS_MATCH", "Proposal, source manifest and retained hash-only manifest match the approved review target."),
    }
    transaction_id = "WSREVIEW-20260927T043904Z-READ-BOUNDARY-001"
    return {
        "transaction_id": transaction_id,
        "transaction_type": TRANSACTION_TYPE,
        "transaction_version": "0.1",
        "proposal_reference": "data/world_state_audit/CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_PENDING.json",
        "proposal_sha256": package["semantic_proposal_fingerprint"],
        "proposal_semantic_fingerprint": package["semantic_proposal_fingerprint"],
        "input_manifest_sha256": package["source_manifest_sha256"],
        "retained_manifest_sha256": package["retained_manifest_sha256"],
        "created_at_utc": reviewed_at_utc,
        "reviewed_at_utc": reviewed_at_utc,
        "reviewer_role": "OPERATOR_HUMAN_REVIEW",
        "decision": decision,
        "decision_scope": DECISION_SCOPE,
        "decision_basis": "Accepted as an accurate, reproducible and appropriately bounded representation of governed evidence available to the v1 reader at the stated cutoff. This does not assert a substantive World State assessment or admit production World State.",
        "criterion_results": criterion_results,
        "proposal_status_after_review": "ACCEPTED_READ_BOUNDARY_CONSISTENCY_ONLY",
        "write_targets": [],
        "public_projection_permitted": False,
        "production_world_state_admitted": False,
        "reviewed_proposal_remains_non_governed": True,
    }


def _decision_markdown(record: dict[str, Any], proposal_path: Path, transaction_path: Path) -> str:
    lines = [
        "# WORLD STATE v1 CONSISTENCY PROPOSAL — HUMAN REVIEW DECISION",
        "",
        "**Decision:** `ACCEPTED`",
        "**Decision scope:** `READ_BOUNDARY_CONSISTENCY_ONLY`",
        "**Transaction type:** `WORLD_STATE_SYNTHESIS_REVIEW`",
        "",
        "This is an explicit human review transaction over non-governed audit evidence. "
        "Acceptance means the retained proposal is an accurate and bounded read of "
        "governed inputs at its cutoff. It is not a substantive World State assessment, "
        "production admission, Actor Registry decision, promotion, or public projection authorization.",
        "",
        f"- Transaction ID: `{record['transaction_id']}`",
        f"- Proposal: `{proposal_path.relative_to(ROOT)}`",
        f"- Proposal semantic fingerprint: `{record['proposal_semantic_fingerprint']}`",
        f"- Source manifest SHA-256: `{record['input_manifest_sha256']}`",
        f"- Retained manifest SHA-256: `{record['retained_manifest_sha256']}`",
        f"- Reviewed at: `{record['reviewed_at_utc']}`",
        "- Reviewer role: `OPERATOR_HUMAN_REVIEW`",
        "- Write targets: `[]`",
        "- Public projection permitted: `false`",
        "- Production World State admitted: `false`",
        "",
        "## Criterion results",
        "",
    ]
    for name, result in record["criterion_results"].items():
        lines.append(f"- `{name}`: `{result['status']}` — `{result['disposition']}`. {result['basis']}")
    lines.extend([
        "",
        "The original `REVIEW_PENDING` proposal and Step 4 summary remain unchanged. "
        "Migration Step 6 remains a separate design decision for a production World State history contract.",
        "",
        f"- Machine-readable transaction: `{transaction_path.relative_to(ROOT)}`",
        "",
    ])
    return "\n".join(lines)


def write_review_record(record: dict[str, Any], *, proposal_path: Path = DEFAULT_PROPOSAL) -> tuple[Path, Path]:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    transaction_path = AUDIT_DIR / "CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_TRANSACTION.json"
    decision_path = AUDIT_DIR / "CONSISTENCY_PROPOSAL_20260927T043904Z_REVIEW_DECISION.md"
    transaction_text = json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    decision_text = _decision_markdown(record, proposal_path, transaction_path)
    for path, text in ((transaction_path, transaction_text), (decision_path, decision_text)):
        if path.exists() and path.read_text(encoding="utf-8") != text:
            raise WorldStateReadError(f"review evidence already exists with different content: {path.relative_to(ROOT)}")
        if not path.exists():
            path.write_text(text, encoding="utf-8")
    return transaction_path, decision_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proposal", type=Path, default=DEFAULT_PROPOSAL)
    parser.add_argument("--decision", required=True, choices=["ACCEPTED"])
    parser.add_argument("--reviewed-at-utc", default=DEFAULT_REVIEWED_AT_UTC)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        proposal_path = args.proposal if args.proposal.is_absolute() else ROOT / args.proposal
        package = json.loads(proposal_path.read_text(encoding="utf-8"))
        record = build_review_transaction(
            package,
            decision=args.decision,
            reviewed_at_utc=args.reviewed_at_utc,
        )
        if args.check_only:
            print(json.dumps(record, indent=2, ensure_ascii=False, sort_keys=True))
            return 0
        transaction_path, decision_path = write_review_record(record, proposal_path=proposal_path)
        print(json.dumps({"status": "PASS", "transaction": str(transaction_path.relative_to(ROOT)), "decision": str(decision_path.relative_to(ROOT)), **record}, indent=2, ensure_ascii=False, sort_keys=True))
        return 0
    except (WorldStateReadError, OSError, json.JSONDecodeError) as exc:
        print(f"World State consistency review FAILED: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
