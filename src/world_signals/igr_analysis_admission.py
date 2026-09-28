"""One bounded Step 14F admission; no retrieval or downstream publication.

Construction is read-only. Materialisation requires the explicit owner decision,
pins the retained package, stages the whole transaction, and rolls back on failure.
"""
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import tempfile

from .analysis import validate_analysis, public_analysis_projection
from .analysis_revision import validate_analysis_revisions
from .live_analysis_bridge import validate_live_analysis_bridge
from .official_projection_candidate import FILES, inspect_step14d, validate_package
from .official_projection_review import step14d_native_extension
from .world_state_history import fingerprint
from .world_state_admission import _atomic_materialize

ANALYSIS_ID = "WSAN-AU-IGR-20260921-001"
REVIEW_ID = "WS-STEP14F-AU-IGR-ANALYSIS-REVIEW-20260929-001"
TRANSACTION_ID = "WS-ANALYSIS-ADMISSION-AU-IGR-20260929-001"
REVIEW_PATH = "data/analysis/STEP14F_AU_IGR_HUMAN_REVIEW_ACCEPTED.json"
TRANSACTION_PATH = "data/analysis/STEP14F_AU_IGR_INTERNAL_ANALYSIS_ADMISSION_TRANSACTION.json"
REVIEWS_PATH = "data/analysis/event_reviews.json"
EVIDENCE_PATH = "data/analysis/evidence_registry.json"
PINS = {
    "analysis_candidate": "2d9756cdad4525e032de1876d5c7057cb7c0caa834ab9d1e6baca58932650e16",
    "projection_inventory": "cc513bdee31bc2b49801a7b222e5972efc4e9b741462536de06b66b32143a1cc",
    "assumption_audit": "1ff8dd0bbe6d88f81d99d61ff57acf0c1ea946bf9e511c330ab5a28d60006138",
    "evidence_manifest": "66b9c667210e0dbdc026f47e9eb7d18f038ce3366db390ef6a6599a2bcf4b9a1",
    "extension_candidate": "c76945773b613206ad58bf597cc6ed02a1e3f646d88fec63e6bce49297cd6c7c",
}
PACKAGE_PIN = "023bb1e0a7bdb9de0c67ab4c4d5203ab0e8d685679e7e75d60dbe1e99ed20da3"
ASSET_PIN = "0fc62cbaf2311aeb7f9bb8d5b884287890159265de39c37fdb956a2cd3245bb9"
EVIDENCE_MAPPING = {
    "WSEV-CANDIDATE-IGR2026-MAIN": "WSEV-AU-IGR-TREASURY-20260921",
    "WSEV-CANDIDATE-IGR2023-MAIN": "WSEV-AU-IGR-TREASURY-20230824",
    "WSEV-CANDIDATE-MINISTER2026": "WSEV-AU-IGR-MINISTERS-20260921",
}
DISPOSITIONS = {
    "analysis": "ACCEPT_INTERNAL_PRODUCTION",
    "official_projection_inventory": "ACCEPT_INTERNAL",
    "assumption_audit": "ACCEPT_INTERNAL",
    "independent_historical_backtest": "DEFER",
    "qualified_historical_comparisons": "RETAIN_SUPPORTING_ONLY",
    "dependency_map": "ACCEPT_INTERNAL_MODEL_STRUCTURE_ONLY",
    **dict.fromkeys(("public_analysis", "relationship_promotion", "world_state_promotion",
                     "forecast_promotion", "scenario_promotion", "risk_promotion"), "NOT_AUTHORISED"),
}


def require(condition, reason):
    if not condition:
        raise ValueError("STEP14F: " + reason)


def load(root, relative):
    return json.loads((root / relative).read_text())


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"


def byte_hash(content):
    return hashlib.sha256(content.encode() if isinstance(content, str) else content).hexdigest()


def seal(value):
    value = deepcopy(value)
    value["transaction_fingerprint"] = fingerprint(value)
    return value


def verify_seal(value):
    require(value.get("transaction_fingerprint") == fingerprint({k: v for k, v in value.items()
            if k != "transaction_fingerprint"}), "audit fingerprint mismatch")


def verify_package(root):
    package = {key: load(root, "data/analysis/" + name) for key, name in FILES.items()}
    result = validate_package(package)
    require({k: v["semantic_fingerprint"] for k, v in package.items()} == PINS, "retained package drift")
    require(result["package_fingerprint"] == PACKAGE_PIN and result["asset_manifest_sha256"] == ASSET_PIN,
            "package/asset manifest drift")
    inspect_step14d(root)  # Exact Canonical/source pins, native validation, manual holds.
    return package


def remap(value):
    if isinstance(value, str):
        return EVIDENCE_MAPPING.get(value, value)
    if isinstance(value, list):
        return [remap(v) for v in value]
    if isinstance(value, dict):
        return {k: remap(v) for k, v in value.items()}
    return value


def validate_datasets(root, reviews, evidence):
    schema = load(root, "data/analysis/schema.json")
    canonical = load(root, "data/canonical/registry.json")
    reports = (validate_analysis(schema, evidence, reviews, canonical),
               validate_analysis_revisions(schema, reviews),
               validate_live_analysis_bridge(schema, reviews, load(root, "data/live_intelligence/observations.json")))
    require(all(r.ok for r in reports), "; ".join(e for r in reports for e in r.errors))
    return public_analysis_projection(schema, evidence, reviews, canonical)


def protected_hashes(root):
    return {str(p.relative_to(root)): byte_hash(p.read_bytes())
            for directory in ("data", "web") for p in sorted((root / directory).rglob("*"))
            if p.is_file() and str(p.relative_to(root)) not in
            {REVIEWS_PATH, EVIDENCE_PATH, REVIEW_PATH, TRANSACTION_PATH}}


def construct(root: Path, reviewed_at_utc: str, admitted_at_utc: str, *, human_decision=None):
    require(human_decision == DISPOSITIONS, "explicit exact owner dispositions required")
    def utc(value):
        require(isinstance(value, str) and value.endswith("Z"), "exact UTC timestamp required")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(utc("2026-09-28T16:25:00Z") <= utc(reviewed_at_utc) <= utc(admitted_at_utc),
            "content cutoff <= human review <= admission required")
    require(not (root / REVIEW_PATH).exists() and not (root / TRANSACTION_PATH).exists(), "admission already exists")
    package = verify_package(root)
    reviews, evidence = load(root, REVIEWS_PATH), load(root, EVIDENCE_PATH)
    require((reviews["version"], len(reviews["reviews"]), evidence["version"], len(evidence["evidence"]))
            == ("0.18", 22, "0.18", 97), "exact admission pre-state required")
    require(not ({r["evidence_id"] for r in evidence["evidence"]} & set(EVIDENCE_MAPPING.values())),
            "permanent evidence identity occupied")
    require(ANALYSIS_ID not in {r["analysis_id"] for r in reviews["reviews"]}, "Analysis already admitted")
    schema = load(root, "data/analysis/schema.json")
    require(schema["version"] == "0.9" and schema.get("review_publication_contract"), "native/publication contract required")
    before = protected_hashes(root)
    # Explicit one-time migration of the 22 already-public reviews, never a default
    # for future population. This exact pre-state and transaction authorise it.
    legacy = deepcopy(reviews)
    legacy["publication_decisions"] = {r["analysis_id"]: "PUBLIC" for r in reviews["reviews"]}
    old_public = validate_datasets(root, legacy, evidence)
    review = seal({"transaction_id": REVIEW_ID, "transaction_type": "ANALYSIS_HUMAN_REVIEW",
        "reviewer_role": "PROJECT_OWNER_EXPLICIT_HUMAN_DECISION", "reviewed_at_utc": reviewed_at_utc,
        "decision_basis": "Owner accepts the exact retained Step 14D material internally; unresolved coverage retained.",
        "candidate_fingerprints": PINS, "package_fingerprint": PACKAGE_PIN,
        "dispositions": deepcopy(human_decision), "visibility": "INTERNAL_ONLY",
        "public_projection_permitted": False, "downstream_write_targets": []})
    row = remap(deepcopy(package["analysis_candidate"]["review"]))
    row["review_state"] = "REVIEWED"
    extension = step14d_native_extension(package)
    extension["admission_review"] = {"human_review_id": REVIEW_ID, "human_review_fingerprint": review["transaction_fingerprint"],
        "independent_historical_backtest_status": "DEFERRED", "historical_comparisons": "SUPPORTING_ONLY",
        "dependency_map_disposition": "INTERNAL_MODEL_STRUCTURE", "model_provenance": deepcopy(package["analysis_candidate"]["model_provenance"])}
    row["official_projection_review"] = extension
    after_reviews = deepcopy(legacy)
    after_reviews["version"] = "0.19"
    after_reviews["reviews"].append(row)
    after_reviews["publication_decisions"][ANALYSIS_ID] = "INTERNAL_ONLY"
    after_evidence = deepcopy(evidence)
    after_evidence["version"] = "0.19"
    after_evidence["evidence"].extend(remap(package["analysis_candidate"]["candidate_local_evidence"]))
    new_public = validate_datasets(root, after_reviews, after_evidence)
    # Only container versions may change; public content, evidence, readiness stay exact.
    a, b = deepcopy(old_public), deepcopy(new_public)
    for projection in (a, b):
        for key in ("review_dataset_version", "evidence_registry_version"):
            projection["metadata"].pop(key, None)
    require(a == b, "legacy public projection changed")
    require(ANALYSIS_ID not in json.dumps(new_public) and
            all(identity not in json.dumps(new_public) for identity in EVIDENCE_MAPPING.values()), "internal leak")
    targets = {REVIEWS_PATH: after_reviews, EVIDENCE_PATH: after_evidence, REVIEW_PATH: review}
    transaction = seal({"transaction_id": TRANSACTION_ID, "transaction_type": "ANALYSIS_INTERNAL_PRODUCTION_ADMISSION",
        "contract_version": "0.1", "analysis_schema_version": schema["version"], "schema_sha256": byte_hash((root / "data/analysis/schema.json").read_bytes()),
        "human_review_id": REVIEW_ID, "human_review_fingerprint": review["transaction_fingerprint"],
        "reviewed_at_utc": reviewed_at_utc, "admitted_at_utc": admitted_at_utc,
        "analysis_as_of_utc": row["analysis_as_of_utc"], "analysis_id": ANALYSIS_ID,
        "candidate_fingerprints": PINS, "package_fingerprint": PACKAGE_PIN, "asset_manifest_sha256": ASSET_PIN,
        "evidence_mapping": EVIDENCE_MAPPING, "production_review_sha256": fingerprint(row),
        "internal_extension_sha256": fingerprint(extension), "publication_decision": "INTERNAL_ONLY",
        "visibility": "INTERNAL_ONLY", "public_projection_permitted": False,
        "pre_state_hashes": {p: byte_hash((root / p).read_bytes()) for p in (REVIEWS_PATH, EVIDENCE_PATH)},
        "post_state_hashes": {p: byte_hash(encoded(v)) for p, v in targets.items()},
        "protected_input_hashes": before, "protected_input_fingerprint": fingerprint(before),
        "legacy_public_semantic_fingerprint": fingerprint(a),
        "write_targets": [REVIEWS_PATH, EVIDENCE_PATH, REVIEW_PATH, TRANSACTION_PATH], "downstream_write_targets": []})
    targets[TRANSACTION_PATH] = transaction
    require(protected_hashes(root) == before, "construction mutated inputs")
    return targets


def validate_admitted(root, *, exact_post_state=False):
    package = verify_package(root)
    review, transaction = load(root, REVIEW_PATH), load(root, TRANSACTION_PATH)
    verify_seal(review); verify_seal(transaction)
    require(review["dispositions"] == DISPOSITIONS and review["transaction_id"] == REVIEW_ID, "human disposition mismatch")
    require(transaction["transaction_id"] == TRANSACTION_ID and transaction["candidate_fingerprints"] == PINS,
            "admission identity/pins mismatch")
    require(transaction["human_review_fingerprint"] == review["transaction_fingerprint"], "human review mismatch")
    require(review["candidate_fingerprints"] == PINS and review["package_fingerprint"] == PACKAGE_PIN
            and transaction["package_fingerprint"] == PACKAGE_PIN and transaction["asset_manifest_sha256"] == ASSET_PIN,
            "retained lineage mismatch")
    require(review["public_projection_permitted"] is False and review["visibility"] == "INTERNAL_ONLY"
            and transaction["publication_decision"] == "INTERNAL_ONLY", "publication authority mismatch")
    times = [datetime.fromisoformat(t.replace("Z", "+00:00")) for t in
             (transaction["analysis_as_of_utc"], review["reviewed_at_utc"], transaction["admitted_at_utc"])]
    require(times[0] <= times[1] <= times[2] and transaction["reviewed_at_utc"] == review["reviewed_at_utc"],
            "review/admission chronology mismatch")
    require(transaction["write_targets"] == [REVIEWS_PATH, EVIDENCE_PATH, REVIEW_PATH, TRANSACTION_PATH]
            and transaction["downstream_write_targets"] == [] and transaction["public_projection_permitted"] is False,
            "admission scope mismatch")
    for p, digest in transaction["post_state_hashes"].items():
        # File hashes prove this transaction's materialisation, not a permanent
        # population ceiling. Later legitimate admissions still pin this exact
        # review/evidence/extension and immutable human record below.
        if exact_post_state or p == REVIEW_PATH:
            require(byte_hash((root / p).read_bytes()) == digest, "post-state mismatch: " + p)
    reviews, evidence = load(root, REVIEWS_PATH), load(root, EVIDENCE_PATH)
    row = next(r for r in reviews["reviews"] if r["analysis_id"] == ANALYSIS_ID)
    expected_spine = remap(package["analysis_candidate"]["review"])
    expected_spine["review_state"] = "REVIEWED"
    require({k: v for k, v in row.items() if k != "official_projection_review"} == expected_spine,
            "accepted analytical spine changed")
    ext = row["official_projection_review"]
    require({k: v for k, v in ext.items() if k != "admission_review"} == step14d_native_extension(package),
            "accepted native extension changed")
    require(ext["admission_review"] == {
        "human_review_id": REVIEW_ID, "human_review_fingerprint": review["transaction_fingerprint"],
        "independent_historical_backtest_status": "DEFERRED", "historical_comparisons": "SUPPORTING_ONLY",
        "dependency_map_disposition": "INTERNAL_MODEL_STRUCTURE",
        "model_provenance": package["analysis_candidate"]["model_provenance"]}, "internal dispositions changed")
    admitted_evidence = [r for r in evidence["evidence"] if r["evidence_id"] in EVIDENCE_MAPPING.values()]
    require(admitted_evidence == remap(package["analysis_candidate"]["candidate_local_evidence"])
            and transaction["evidence_mapping"] == EVIDENCE_MAPPING, "evidence mapping changed")
    require(fingerprint(row) == transaction["production_review_sha256"] and
            fingerprint(row["official_projection_review"]) == transaction["internal_extension_sha256"], "production object mismatch")
    require(row["review_state"] == "REVIEWED" and reviews["publication_decisions"][ANALYSIS_ID] == "INTERNAL_ONLY", "review/publication mismatch")
    return validate_datasets(root, reviews, evidence)


def materialize(root, targets):
    require(set(targets) == {REVIEWS_PATH, EVIDENCE_PATH, REVIEW_PATH, TRANSACTION_PATH}, "exact bounded targets required")
    transaction = targets[TRANSACTION_PATH]
    require(protected_hashes(root) == transaction["protected_input_hashes"], "protected pre-state changed")
    require(all(byte_hash((root / p).read_bytes()) == h for p, h in transaction["pre_state_hashes"].items()), "pre-state changed")
    require(not (root / REVIEW_PATH).exists() and not (root / TRANSACTION_PATH).exists(), "audit target occupied")
    # Validate the exact staged transaction on an isolated repository copy first.
    import shutil
    with tempfile.TemporaryDirectory(prefix="ws14f-simulation-") as directory:
        staged = Path(directory)
        for d in ("data", "web"):
            shutil.copytree(root / d, staged / d)
        _atomic_materialize({staged / p: encoded(v) for p, v in targets.items()})
        validate_admitted(staged, exact_post_state=True)
    require(protected_hashes(root) == transaction["protected_input_hashes"] and
            all(byte_hash((root / p).read_bytes()) == h for p, h in transaction["pre_state_hashes"].items()),
            "pre-state changed during simulation")
    originals = {root / p: (root / p).read_bytes() if (root / p).exists() else None for p in targets}
    try:
        _atomic_materialize({root / p: encoded(v) for p, v in targets.items()})
        validate_admitted(root, exact_post_state=True)
        require(protected_hashes(root) == transaction["protected_input_hashes"], "protected inputs mutated")
    except Exception:
        for p, content in originals.items():
            if content is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(content)
        raise
