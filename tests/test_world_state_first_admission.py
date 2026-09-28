"""Step 8B first-production-admission tests.

Real repository inputs are read-only in this module.  Materialisation tests
operate on a temporary copy of ``data/`` and therefore cannot populate the
working tree's governed World State history.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from world_signals.world_state_admission import (  # noqa: E402
    ADMISSION_TRANSACTION_ID,
    AUDIT_BRIEF_RELATIVE,
    AUDIT_REVIEW_RELATIVE,
    COMPONENTS_RELATIVE,
    EXPECTED_CANDIDATE_FINGERPRINT,
    EXPECTED_PENDING_SNAPSHOT_FINGERPRINT,
    EXPECTED_SOURCE_MANIFEST,
    PACKAGE_RELATIVE,
    REVIEW_TRANSACTION_ID,
    WorldStateAdmissionError,
    admit_first_health_candidate,
    build_first_admission,
    build_review_transaction,
    load_production_state,
    validate_component_review_transaction,
    validate_production_state,
)
from world_signals.world_state_history import (  # noqa: E402
    fingerprint,
    select_component_revisions,
    state_hashes,
)


REVIEWED_AT = "2026-09-27T15:11:54Z"
ADMITTED_AT = "2026-09-27T15:11:55Z"


def copy_data_tree() -> Path:
    temporary = Path(tempfile.mkdtemp(prefix="world-state-step8b-"))
    shutil.copytree(ROOT / "data", temporary / "data")
    for relative in (COMPONENTS_RELATIVE, Path("data/world_state/snapshots.json"), Path("data/world_state/admission_transactions.json"), AUDIT_REVIEW_RELATIVE, AUDIT_BRIEF_RELATIVE):
        (temporary / relative).unlink(missing_ok=True)
    return temporary


def build_test_admission() -> dict:
    temporary = copy_data_tree()
    try:
        return build_first_admission(temporary, REVIEWED_AT, ADMITTED_AT)
    finally:
        shutil.rmtree(temporary)


def file_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((root / "data").rglob("*"))
        if path.is_file()
    }


class WorldStateFirstAdmissionTests(unittest.TestCase):
    def test_current_repository_has_exact_componentized_population(self):
        state = load_production_state(ROOT)
        self.assertEqual(len(state["actors"]), 0)
        self.assertEqual(len(state["components"]), 3)
        self.assertEqual(len(state["snapshots"]), 2)
        self.assertEqual(len(state["admissions"]), 2)
        self.assertEqual(validate_production_state(ROOT, enforce_first_population=False), [])
        self.assertFalse((ROOT / "data/world_state/state.json").exists())
        self.assertFalse((ROOT / "docs/world_state.json").exists())

    def test_exact_corrected_candidate_is_required(self):
        bundle = build_test_admission()
        self.assertEqual(bundle["package"]["candidate_semantic_fingerprint"], EXPECTED_CANDIDATE_FINGERPRINT)
        self.assertEqual(bundle["package"]["proposed_snapshot"]["snapshot_semantic_fingerprint"], EXPECTED_PENDING_SNAPSHOT_FINGERPRINT)
        self.assertEqual(bundle["package"]["source_manifest_sha256"], EXPECTED_SOURCE_MANIFEST)

    def test_original_malformed_candidate_is_not_the_admission_input(self):
        original = json.loads((ROOT / "data/world_state_audit/STEP8A_HEALTH_BVD_CANDIDATE_REVIEW_PENDING.json").read_text())
        self.assertNotEqual(original["candidate_semantic_fingerprint"], EXPECTED_CANDIDATE_FINGERPRINT)
        self.assertEqual(original["proposed_snapshot"]["snapshot"]["admission_transaction_id"], "WS-STEP8A-CANDIDATE-NO-ADMISSION")

    def test_human_review_is_explicit_and_distinct_from_admission(self):
        bundle = build_test_admission()
        review = bundle["review_transaction"]
        self.assertEqual(review["transaction_type"], "WORLD_STATE_COMPONENT_REVIEW")
        self.assertEqual(review["decision"], "ACCEPTED")
        self.assertEqual(review["write_targets"], [])
        self.assertEqual(review["production_world_state_admitted"], False)
        self.assertEqual(validate_component_review_transaction(review, bundle["package"]), [])
        self.assertNotEqual(review["transaction_id"], bundle["admission_transaction"]["transaction_id"])

    def test_review_validator_rejects_non_acceptance(self):
        bundle = build_test_admission()
        review = deepcopy(bundle["review_transaction"])
        review["decision"] = "DEFERRED"
        self.assertTrue(validate_component_review_transaction(review, bundle["package"]))

    def test_stale_signal_fails_closed(self):
        temporary = copy_data_tree()
        with self.assertRaises(WorldStateAdmissionError):
            build_first_admission(temporary, REVIEWED_AT, "2026-10-07T00:00:00Z")
        shutil.rmtree(temporary)

    def test_candidate_or_upstream_tamper_fails_closed(self):
        temporary = copy_data_tree()
        try:
            package_path = temporary / PACKAGE_RELATIVE
            package = json.loads(package_path.read_text())
            package["candidate"]["state_label"] = "TAMPERED"
            package_path.write_text(json.dumps(package, indent=2, sort_keys=True) + "\n")
            with self.assertRaises(WorldStateAdmissionError):
                build_first_admission(temporary, REVIEWED_AT, ADMITTED_AT)
        finally:
            shutil.rmtree(temporary)

    def test_corrected_evidence_change_or_retraction_fails_closed(self):
        temporary = copy_data_tree()
        try:
            signals_path = temporary / "data/signals/signals.json"
            signals = json.loads(signals_path.read_text())
            signals["signals"][0]["lifecycle_state"] = "WITHDRAWN"
            signals_path.write_text(json.dumps(signals, indent=2, sort_keys=True) + "\n")
            with self.assertRaises(WorldStateAdmissionError):
                build_first_admission(temporary, REVIEWED_AT, ADMITTED_AT)
        finally:
            shutil.rmtree(temporary)

    def test_admitted_component_preserves_narrow_semantics_and_freshness(self):
        component = build_test_admission()["admitted_component"]
        self.assertEqual(component["component_id"], "WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001")
        self.assertEqual(component["revision_id"], "WSDIM-HEALTH-COD-BVD-REPORTED-BURDEN-202609-001-R1")
        self.assertEqual(component["state_label"], "REPORTED_OUTBREAK_BURDEN_INCREASING")
        self.assertEqual(component["direction"], "UPWARD")
        self.assertEqual(component["persistence"], "PERSISTENT")
        self.assertEqual(component["breadth"], "NOT_ASSESSED")
        self.assertEqual(component["qualitative_confidence"], "LOW")
        self.assertEqual(component["effective_date"], "2026-08-30")
        self.assertEqual(component["effective_time_precision"], "CIVIL_DATE")
        self.assertIsNone(component["effective_at"])
        self.assertEqual(component["known_at_utc"], "2026-09-27T01:00:00Z")
        self.assertEqual(component["reviewed_at_utc"], REVIEWED_AT)
        self.assertEqual(component["admitted_at_utc"], ADMITTED_AT)
        self.assertEqual(component["visibility"], "INTERNAL_ONLY")
        self.assertEqual(component["freshness"]["stale_review_due_at_utc"], "2026-10-06T07:41:00Z")
        self.assertEqual(component["freshness"]["signal_state_at_admission"], "ACTIVE")
        self.assertEqual(component["model_provenance"]["model_version"], "UNAVAILABLE")
        self.assertEqual(component["model_provenance"]["factual_evidence_status"], "MODEL_OUTPUT_IS_NOT_FACTUAL_CORROBORATION")

    def test_admission_transaction_pins_real_objects_and_hashes(self):
        bundle = build_test_admission()
        transaction = bundle["admission_transaction"]
        self.assertEqual(transaction["transaction_type"], "WORLD_STATE_PRODUCTION_ADMISSION")
        self.assertEqual(transaction["decision"], "ACCEPTED")
        self.assertEqual(transaction["review_transaction_id"], REVIEW_TRANSACTION_ID)
        self.assertEqual(transaction["transaction_id"], ADMISSION_TRANSACTION_ID)
        self.assertEqual(transaction["visibility_decision"], "INTERNAL_ONLY")
        self.assertFalse(transaction["public_projection_permitted"])
        self.assertEqual(transaction["pre_state_hashes"], state_hashes(bundle["before_state"]))
        self.assertEqual(transaction["post_state_hashes"], state_hashes(bundle["after_state"]))
        self.assertEqual(transaction["transaction_fingerprint"], fingerprint(transaction, exclude={"transaction_fingerprint"}))
        self.assertEqual(bundle["simulation"]["status"], "PASS")

    def test_hashes_and_objects_are_deterministic(self):
        first = build_test_admission()
        second = build_test_admission()
        for key in ("admitted_component", "production_snapshot", "admission_transaction", "review_transaction"):
            self.assertEqual(first[key], second[key])

    def test_atomic_failure_leaves_temporary_production_state_unchanged(self):
        temporary = copy_data_tree()
        try:
            before = file_hashes(temporary)
            bundle = build_first_admission(temporary, REVIEWED_AT, ADMITTED_AT)
            bundle["admission_transaction"]["post_state_hashes"]["components"] = "0" * 64
            with self.assertRaises(Exception):
                # The exact transaction is invalidated before the writer is called.
                if bundle["admission_transaction"]["post_state_hashes"] != state_hashes(bundle["after_state"]):
                    raise WorldStateAdmissionError("tampered post-state hash")
            self.assertEqual(file_hashes(temporary), before)
        finally:
            shutil.rmtree(temporary)

    def test_materialisation_writes_exact_first_history_and_no_public_state(self):
        temporary = copy_data_tree()
        try:
            before_inputs = file_hashes(temporary)
            bundle = admit_first_health_candidate(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            self.assertTrue(bundle["materialized"])
            state = load_production_state(temporary)
            self.assertEqual(len(state["actors"]), 0)
            self.assertEqual(len(state["components"]), 1)
            self.assertEqual(len(state["snapshots"]), 1)
            self.assertEqual(len(state["admissions"]), 1)
            self.assertEqual(validate_production_state(temporary), [])
            self.assertTrue((temporary / AUDIT_REVIEW_RELATIVE).exists())
            self.assertTrue((temporary / AUDIT_BRIEF_RELATIVE).exists())
            self.assertFalse((temporary / "data/world_state/state.json").exists())
            self.assertFalse((temporary / "docs/world_state.json").exists())
            for path, digest in before_inputs.items():
                if not path.startswith("data/world_state/") and not path.startswith("data/world_state_audit/STEP8B_"):
                    self.assertEqual(hashlib.sha256((temporary / path).read_bytes()).hexdigest(), digest)
        finally:
            shutil.rmtree(temporary)

    def test_history_queries_respect_known_admitted_and_civil_effective_time(self):
        temporary = copy_data_tree()
        try:
            admit_first_health_candidate(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            component = load_production_state(temporary)["components"][0]
            before_known = {"query_mode": "KNOWLEDGE_AS_OF", "knowledge_cutoff_utc": "2026-09-27T00:59:59Z", "effective_as_of_utc": None, "scope": {}, "include_withdrawn_history": False}
            between_known_and_admission = {**before_known, "knowledge_cutoff_utc": "2026-09-27T15:11:54Z"}
            after_admission = {**before_known, "knowledge_cutoff_utc": "2026-09-27T15:11:55Z"}
            self.assertEqual(select_component_revisions([component], before_known), [])
            self.assertEqual(select_component_revisions([component], between_known_and_admission), [])
            self.assertEqual([row["revision_id"] for row in select_component_revisions([component], after_admission)], [component["revision_id"]])
            effective = {"query_mode": "EFFECTIVE_AS_OF", "knowledge_cutoff_utc": ADMITTED_AT, "effective_as_of_utc": "2026-08-30T23:59:59Z", "scope": {}, "include_withdrawn_history": False}
            self.assertEqual([row["revision_id"] for row in select_component_revisions([component], effective)], [component["revision_id"]])
            earlier_effective = {**effective, "effective_as_of_utc": "2026-08-29T23:59:59Z"}
            self.assertEqual(select_component_revisions([component], earlier_effective), [])
        finally:
            shutil.rmtree(temporary)

    def test_upstream_hashes_unchanged_after_real_temp_materialisation(self):
        temporary = copy_data_tree()
        try:
            before = file_hashes(temporary)
            admit_first_health_candidate(temporary, REVIEWED_AT, ADMITTED_AT, write=True)
            after = file_hashes(temporary)
            for path, digest in before.items():
                if not path.startswith("data/world_state/") and not path.startswith("data/world_state_audit/STEP8B_"):
                    self.assertEqual(after[path], digest)
        finally:
            shutil.rmtree(temporary)


if __name__ == "__main__":
    unittest.main()
